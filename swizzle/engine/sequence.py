"""
Swizzle Continuous Batching Engine: Sequence and Request Representation.

Tracks prompt tokens, generated output tokens, logical-to-physical block tables,
sampling parameters, and AST semantic hash metadata across decode iterations.
"""

from enum import Enum
from typing import List, Optional, Set, Dict, Any
import time


class SequenceStatus(Enum):
    WAITING = "WAITING"
    RUNNING = "RUNNING"
    SWAPPED = "SWAPPED"
    FINISHED_STOPPED = "FINISHED_STOPPED"
    FINISHED_LENGTH_CAPPED = "FINISHED_LENGTH_CAPPED"
    FINISHED_ABORTED = "FINISHED_ABORTED"

    @classmethod
    def is_finished(cls, status: "SequenceStatus") -> bool:
        return status in (
            cls.FINISHED_STOPPED,
            cls.FINISHED_LENGTH_CAPPED,
            cls.FINISHED_ABORTED,
        )


class SamplingParams:
    def __init__(
        self,
        temperature: float = 1.0,
        top_p: float = 1.0,
        max_tokens: int = 256,
        stop_tokens: Optional[Set[int]] = None,
        ignore_eos: bool = False,
        speculative_draft_tokens: int = 4,
    ):
        self.temperature = max(1e-5, temperature)
        self.top_p = min(max(1e-5, top_p), 1.0)
        self.max_tokens = max_tokens
        self.stop_tokens = stop_tokens or set()
        self.ignore_eos = ignore_eos
        self.speculative_draft_tokens = speculative_draft_tokens


class Sequence:
    def __init__(
        self,
        seq_id: int,
        prompt_tokens: List[int],
        block_size: int = 16,
    ):
        self.seq_id = seq_id
        self.prompt_tokens = list(prompt_tokens)
        self.output_tokens: List[int] = []
        self.cumulative_logprob: float = 0.0
        self.status: SequenceStatus = SequenceStatus.WAITING
        self.block_size = block_size
        self.block_table: List[int] = []  # Physical block IDs allocated to this sequence
        self.ast_hashes: List[str] = []   # AST content hashes per block

    def get_len(self) -> int:
        return len(self.prompt_tokens) + len(self.output_tokens)

    def get_prompt_len(self) -> int:
        return len(self.prompt_tokens)

    def get_output_len(self) -> int:
        return len(self.output_tokens)

    def get_token_ids(self) -> List[int]:
        return self.prompt_tokens + self.output_tokens

    def get_last_token_id(self) -> int:
        if self.output_tokens:
            return self.output_tokens[-1]
        return self.prompt_tokens[-1] if self.prompt_tokens else 0

    def append_token_id(self, token_id: int, logprob: float = 0.0) -> None:
        self.output_tokens.append(token_id)
        self.cumulative_logprob += logprob

    def is_finished(self) -> bool:
        return SequenceStatus.is_finished(self.status)

    def num_blocks(self) -> int:
        total = self.get_len()
        return (total + self.block_size - 1) // self.block_size


class SequenceGroup:
    def __init__(
        self,
        request_id: str,
        seqs: List[Sequence],
        sampling_params: SamplingParams,
        arrival_time: Optional[float] = None,
        ast_metadata: Optional[Dict[str, Any]] = None,
    ):
        self.request_id = request_id
        self.seqs = seqs
        self.sampling_params = sampling_params
        self.arrival_time = arrival_time or time.time()
        self.ast_metadata = ast_metadata or {}

    def is_finished(self) -> bool:
        return all(seq.is_finished() for seq in self.seqs)

    def get_first_seq(self) -> Sequence:
        return self.seqs[0]

    def get_max_len(self) -> int:
        return max(seq.get_len() for seq in self.seqs)
