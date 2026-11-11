"""
Swizzle Continuous Batching Engine: Base Model Backend Protocol.

Defines the contract for model runners executing causal language model forward passes,
tokenization, next-token sampling, and KV-cache block manipulation.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
import numpy as np


class BaseModelBackend(ABC):
    """Abstract protocol for causal language model inference runners."""

    @abstractmethod
    def forward(
        self,
        input_ids: List[int],
        block_tables: Optional[List[List[int]]] = None,
        is_prefill: bool = False,
    ) -> List[float]:
        """
        Executes causal forward pass for the given token sequence.
        Returns the unnormalized logit distribution over the model vocabulary for the next token.
        """
        pass

    def sample_next_token(
        self,
        logits: List[float],
        temperature: float = 1.0,
        top_p: float = 1.0,
    ) -> int:
        """
        Samples next token ID from logit distribution using temperature and top-p (nucleus) filtering.
        """
        logits_arr = np.array(logits, dtype=np.float32)
        if temperature > 1e-4:
            logits_arr = logits_arr / float(temperature)

        # Numerically stable softmax
        shift_logits = logits_arr - np.max(logits_arr)
        exp_logits = np.exp(shift_logits)
        probs = exp_logits / np.sum(exp_logits)

        # Nucleus (top-p) truncation
        if top_p < 1.0:
            sorted_indices = np.argsort(probs)[::-1]
            sorted_probs = probs[sorted_indices]
            cumulative_probs = np.cumsum(sorted_probs)
            cutoff = cumulative_probs > top_p
            if np.any(cutoff):
                first_cutoff = np.argmax(cutoff)
                if first_cutoff > 0:
                    sorted_probs[first_cutoff + 1:] = 0.0
                    probs = np.zeros_like(probs)
                    probs[sorted_indices] = sorted_probs
                    p_sum = np.sum(probs)
                    if p_sum > 0:
                        probs /= p_sum

        token_idx = int(np.random.choice(len(probs), p=probs))
        return token_idx

    @abstractmethod
    def tokenize(self, text: str) -> List[int]:
        """Converts UTF-8 text into a sequence of vocabulary token IDs."""
        pass

    @abstractmethod
    def detokenize(self, token_ids: List[int]) -> str:
        """Converts a sequence of token IDs into UTF-8 text."""
        pass

    @property
    @abstractmethod
    def vocab_size(self) -> int:
        """Returns the vocabulary size of the model."""
        pass

