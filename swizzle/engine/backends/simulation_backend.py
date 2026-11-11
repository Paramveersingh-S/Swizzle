"""
Swizzle Continuous Batching Engine: Simulation Backend.

Provides deterministic, zero-dependency model forward passes for continuous batching,
scheduler stress-testing, and virtual block manager validation on CPU / CI.
"""

from typing import List, Optional
import numpy as np
from .base import BaseModelBackend


class SimulationBackend(BaseModelBackend):
    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
        vocab_size: int = 152064,
    ):
        self.model_name = model_name
        self._vocab_size = vocab_size

    @property
    def vocab_size(self) -> int:
        return self._vocab_size

    def forward(
        self,
        input_ids: List[int],
        block_tables: Optional[List[List[int]]] = None,
        is_prefill: bool = False,
    ) -> List[float]:
        # Deterministic seed based on last tokens to ensure reproducible verification
        seed = hash(tuple(input_ids[-4:])) % (2**31 - 1) if input_ids else 42
        rng = np.random.RandomState(seed=seed)

        # Standard normal distribution over vocabulary
        logits = rng.normal(loc=0.0, scale=1.0, size=self._vocab_size).astype(np.float32)

        # Boost top-5 tokens to simulate confident causal LM predictions
        top_k = rng.choice(self._vocab_size, size=5, replace=False)
        logits[top_k] += 12.0

        return logits.tolist()

    def tokenize(self, text: str) -> List[int]:
        # Fast byte offset tokenizer for simulation
        return [int(b) + 1 for b in text.encode("utf-8")]

    def detokenize(self, token_ids: List[int]) -> str:
        byte_vals = bytes([max(0, min(255, int(t) - 1)) for t in token_ids])
        return byte_vals.decode("utf-8", errors="replace")

