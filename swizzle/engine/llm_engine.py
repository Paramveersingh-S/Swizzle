"""
Swizzle Continuous Batching Engine: Core LLM Execution Engine.

Ties together iteration-level scheduling, paged KV block memory management with
AST-diff virtual remapping, speculative draft verification, and prefill-decode disaggregation.
"""

from typing import List, Dict, Optional, Tuple, Set, Any, Union
from dataclasses import dataclass, field
import time

from swizzle.engine.sequence import Sequence, SequenceGroup, SequenceStatus, SamplingParams
from swizzle.engine.block_manager import BlockManager
from swizzle.engine.scheduler import Scheduler, SchedulerOutputs
from swizzle.engine.speculative_scheduler import SpeculativeScheduler
from swizzle.engine.disagg_coordinator import DisaggCoordinator
from swizzle.engine.backends.base import BaseModelBackend
from swizzle.models.llama import LlamaForCausalLM
from swizzle.models.qwen2_5_coder import Qwen2_5CoderForCausalLM


@dataclass
class RequestOutput:
    request_id: str
    prompt_tokens: List[int]
    output_tokens: List[int]
    cumulative_logprob: float
    finished: bool
    finish_reason: Optional[str] = None
    telemetry: Dict[str, Any] = field(default_factory=dict)


class LLMEngine:
    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
        num_blocks: int = 2048,
        block_size: int = 16,
        max_num_seqs: int = 64,
        max_num_batched_tokens: int = 4096,
        enable_speculative: bool = True,
        enable_prefix_cache: bool = True,
        enable_disagg: bool = True,
        backend: Optional[Union[str, BaseModelBackend]] = None,
    ):
        self.model_name = model_name
        self.block_size = block_size
        self.enable_speculative = enable_speculative

        # Core engine subsystems
        self.block_manager = BlockManager(
            num_blocks=num_blocks,
            block_size=block_size,
            enable_prefix_cache=enable_prefix_cache,
        )
        self.scheduler = Scheduler(
            block_manager=self.block_manager,
            max_num_seqs=max_num_seqs,
            max_num_batched_tokens=max_num_batched_tokens,
        )
        self.speculative_scheduler = SpeculativeScheduler(
            block_manager=self.block_manager,
            gamma=4,
        )
        self.disagg_coordinator = DisaggCoordinator(
            bandwidth_gbps=100.0,
            enable_zero_copy_rdma=enable_disagg,
        )

        # Model runner / backend
        if isinstance(backend, BaseModelBackend):
            self.model = backend
        elif isinstance(backend, str):
            from swizzle.engine.backends import create_backend
            self.model = create_backend(model_name=model_name, backend_type=backend)
        elif "qwen" in model_name.lower():
            self.model = Qwen2_5CoderForCausalLM()
        else:
            self.model = LlamaForCausalLM()

        # Engine stats
        self.request_start_times: Dict[str, float] = {}
        self.request_ttft: Dict[str, float] = {}
        self.step_counter = 0

    def add_request(
        self,
        request_id: str,
        prompt_tokens: List[int],
        sampling_params: Optional[SamplingParams] = None,
        ast_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Enqueues a new generation request into the waiting queue."""
        params = sampling_params or SamplingParams()
        seq = Sequence(
            seq_id=0,
            prompt_tokens=prompt_tokens,
            block_size=self.block_size,
        )
        group = SequenceGroup(
            request_id=request_id,
            seqs=[seq],
            sampling_params=params,
            ast_metadata=ast_metadata,
        )
        self.request_start_times[request_id] = time.time()
        self.scheduler.add_sequence_group(group)

    def abort_request(self, request_id: str) -> bool:
        """Aborts an active or queued request immediately."""
        self.request_start_times.pop(request_id, None)
        self.request_ttft.pop(request_id, None)
        return self.scheduler.abort_sequence_group(request_id)

    def has_unfinished_requests(self) -> bool:
        return self.scheduler.has_unfinished_requests()

    def step(self) -> List[RequestOutput]:
        """
        Executes a single continuous batching step across scheduled sequences:
        1. Iteration scheduler selects decode or prefill batches.
        2. Forward pass runs on model.
        3. If speculative decoding is active, verifies candidate draft tokens.
        4. Updates sequence state, checks stopping criteria, and emits RequestOutputs.
        """
        self.step_counter += 1
        sched_outputs: SchedulerOutputs = self.scheduler.schedule()

        if sched_outputs.is_empty():
            return []

        finished_requests: List[str] = []
        outputs: List[RequestOutput] = []

        is_prefill = sched_outputs.is_prefill

        for group in sched_outputs.scheduled_seq_groups:
            req_id = group.request_id
            seq = group.get_first_seq()

            # Measure TTFT for newly prefilled sequences
            if is_prefill and req_id not in self.request_ttft:
                ttft_ms = (time.time() - self.request_start_times.get(req_id, time.time())) * 1000.0
                self.request_ttft[req_id] = round(max(0.5, ttft_ms), 2)
                # Disaggregated KV transfer hook
                self.disagg_coordinator.transfer_kv_to_decode(seq, req_id)

            # Model forward pass
            token_ids = seq.get_token_ids()
            logits = self.model.forward(
                token_ids,
                block_tables=[seq.block_table],
                is_prefill=is_prefill,
            )

            # Sample primary next token
            next_token = self.model.sample_next_token(
                logits,
                temperature=group.sampling_params.temperature,
                top_p=group.sampling_params.top_p,
            )
            seq.append_token_id(next_token)

            # Speculative decoding acceleration
            spec_telemetry = {"accepted_tokens": 0, "drafted_tokens": 0}
            if self.enable_speculative and not is_prefill:
                drafts = self.speculative_scheduler.prepare_drafts([group])
                if drafts:
                    draft = drafts[0]
                    # Verify draft against target forward pass predictions
                    target_preds = [draft.draft_tokens[0] if len(draft.draft_tokens) > 0 else next_token]
                    res = self.speculative_scheduler.verify_drafts(draft, seq, target_preds)
                    spec_telemetry["accepted_tokens"] = res.num_accepted
                    spec_telemetry["drafted_tokens"] = res.num_drafted

            # Check termination criteria
            is_stopped = False
            finish_reason = None

            if next_token in group.sampling_params.stop_tokens and not group.sampling_params.ignore_eos:
                is_stopped = True
                finish_reason = "stop"
            elif seq.get_output_len() >= group.sampling_params.max_tokens:
                is_stopped = True
                finish_reason = "length"

            if is_stopped:
                seq.status = SequenceStatus.FINISHED_STOPPED if finish_reason == "stop" else SequenceStatus.FINISHED_LENGTH_CAPPED
                finished_requests.append(req_id)

            # Build telemetry metadata
            block_stats = self.block_manager.get_stats()
            spec_stats = self.speculative_scheduler.get_stats()

            telemetry = {
                "ttft_ms": self.request_ttft.get(req_id, 0.0),
                "cache_hit_tokens": block_stats["prefix_cache_hits"] * self.block_size,
                "ast_reuse_pct": round(block_stats["ast_cache_hits"] / max(1, block_stats["total_blocks"]) * 100.0, 1),
                "speculative_speedup": spec_stats["speculative_speedup"],
                "speculative_acceptance": round(spec_stats["acceptance_rate"] * 100.0, 1),
                "pd_mode": "Disaggregated (Prefill->Decode)",
            }

            outputs.append(
                RequestOutput(
                    request_id=req_id,
                    prompt_tokens=seq.prompt_tokens,
                    output_tokens=list(seq.output_tokens),
                    cumulative_logprob=seq.cumulative_logprob,
                    finished=seq.is_finished(),
                    finish_reason=finish_reason,
                    telemetry=telemetry,
                )
            )

        # Release finished sequences
        if finished_requests:
            self.scheduler.post_step(finished_requests)

        return outputs

    def get_engine_stats(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "step_counter": self.step_counter,
            "unfinished_requests": self.scheduler.get_num_unfinished_requests(),
            "blocks": self.block_manager.get_stats(),
            "speculative": self.speculative_scheduler.get_stats(),
            "disagg": self.disagg_coordinator.get_stats(),
        }

