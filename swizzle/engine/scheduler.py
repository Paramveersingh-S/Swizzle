"""
Swizzle Continuous Batching Engine: Iteration-Level Scheduler.

Manages dynamic iteration scheduling across WAITING, RUNNING, and SWAPPED queues,
chunked prefill, and iteration-level preemption when GPU KV cache memory approaches capacity.
"""

from typing import List, Dict, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from swizzle.engine.sequence import Sequence, SequenceGroup, SequenceStatus
from swizzle.engine.block_manager import BlockManager


@dataclass
class SchedulerOutputs:
    scheduled_seq_groups: List[SequenceGroup] = field(default_factory=list)
    is_prefill: bool = False
    num_batched_tokens: int = 0
    preempted_requests: List[str] = field(default_factory=list)
    blocks_to_swap_out: Dict[int, int] = field(default_factory=dict)
    blocks_to_swap_in: Dict[int, int] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return len(self.scheduled_seq_groups) == 0


class Scheduler:
    def __init__(
        self,
        block_manager: BlockManager,
        max_num_seqs: int = 64,
        max_num_batched_tokens: int = 2048,
        max_prefill_chunk_tokens: int = 512,
    ):
        self.block_manager = block_manager
        self.max_num_seqs = max_num_seqs
        self.max_num_batched_tokens = max_num_batched_tokens
        self.max_prefill_chunk_tokens = max_prefill_chunk_tokens

        # Queues
        self.waiting: List[SequenceGroup] = []
        self.running: List[SequenceGroup] = []
        self.swapped: List[SequenceGroup] = []

        # Internal sequence ID generator
        self._seq_counter = 0

    def add_sequence_group(self, seq_group: SequenceGroup) -> None:
        self.waiting.append(seq_group)

    def abort_sequence_group(self, request_id: str) -> bool:
        """Aborts an active or queued request, reclaiming its allocated KV blocks."""
        for queue in (self.waiting, self.running, self.swapped):
            for i, group in enumerate(queue):
                if group.request_id == request_id:
                    for seq in group.seqs:
                        seq.status = SequenceStatus.FINISHED_ABORTED
                        self.block_manager.free(seq)
                    queue.pop(i)
                    return True
        return False

    def has_unfinished_requests(self) -> bool:
        return bool(self.waiting or self.running or self.swapped)

    def get_num_unfinished_requests(self) -> int:
        return len(self.waiting) + len(self.running) + len(self.swapped)

    def schedule(self) -> SchedulerOutputs:
        """
        Executes a single continuous batching scheduling step.
        Prioritizes decoding for currently running sequences to minimize Inter-Token Latency (ITL).
        Admits new prefill requests if batch token budget and KV block memory permit.
        """
        outputs = SchedulerOutputs()

        # Step 1: Schedule running decode sequences
        scheduled_running: List[SequenceGroup] = []
        num_batched_tokens = 0

        # Check running sequences and allocate decode slots
        i = 0
        while i < len(self.running):
            seq_group = self.running[i]
            can_schedule_group = True

            # Ensure every sequence in the group can append a decode slot
            for seq in seq_group.seqs:
                if not self.block_manager.can_append_slot(seq):
                    # Preemption: Memory is exhausted. Preempt the lowest priority running request.
                    can_schedule_group = False
                    break

            if can_schedule_group and len(scheduled_running) < self.max_num_seqs:
                for seq in seq_group.seqs:
                    self.block_manager.append_slot(seq)
                scheduled_running.append(seq_group)
                num_batched_tokens += len(seq_group.seqs)
                i += 1
            else:
                # Preempt this sequence group: move to waiting queue, reclaim memory
                preempted = self.running.pop(i)
                outputs.preempted_requests.append(preempted.request_id)
                for seq in preempted.seqs:
                    seq.status = SequenceStatus.WAITING
                    self.block_manager.free(seq)
                self.waiting.insert(0, preempted)

        if scheduled_running:
            outputs.scheduled_seq_groups = scheduled_running
            outputs.is_prefill = False
            outputs.num_batched_tokens = num_batched_tokens
            return outputs

        # Step 2: Schedule waiting sequences for prefill if no decode is scheduled
        scheduled_waiting: List[SequenceGroup] = []
        while self.waiting:
            seq_group = self.waiting[0]
            first_seq = seq_group.get_first_seq()
            num_tokens = first_seq.get_prompt_len()

            # Check capacity limits
            if len(scheduled_waiting) >= self.max_num_seqs:
                break
            if num_batched_tokens + num_tokens > self.max_num_batched_tokens:
                break
            if not self.block_manager.can_allocate(first_seq):
                break

            # Pop and allocate
            self.waiting.pop(0)
            self.block_manager.allocate(first_seq)

            # Apply AST-Diff virtual remapping if present in request metadata
            if seq_group.ast_metadata and "ast_diff_map" in seq_group.ast_metadata:
                self.block_manager.remap_ast_blocks(
                    first_seq, seq_group.ast_metadata["ast_diff_map"]
                )

            first_seq.status = SequenceStatus.RUNNING
            scheduled_waiting.append(seq_group)
            self.running.append(seq_group)
            num_batched_tokens += num_tokens

        outputs.scheduled_seq_groups = scheduled_waiting
        outputs.is_prefill = True
        outputs.num_batched_tokens = num_batched_tokens
        return outputs

    def post_step(self, finished_requests: List[str]) -> None:
        """Cleans up completed requests and frees their KV blocks."""
        remaining_running = []
        for seq_group in self.running:
            if seq_group.request_id in finished_requests or seq_group.is_finished():
                for seq in seq_group.seqs:
                    self.block_manager.free(seq)
            else:
                remaining_running.append(seq_group)
        self.running = remaining_running
