"""
Swizzle Continuous Batching Engine: Llama.cpp Backend.

Enables local low-memory quantized GGUF inference (e.g. 1B-3B models)
on edge workstations or laptops via llama-cpp-python.
"""

from typing import List, Optional
from .base import BaseModelBackend


class LlamaCppBackend(BaseModelBackend):
    def __init__(
        self,
        model_path: str = "models/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,
        vocab_size: int = 128256,
        **kwargs,
    ):
        self.model_path = model_path
        self._vocab_size = vocab_size
        self._llm = None
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.kwargs = kwargs

    def _ensure_loaded(self):
        if self._llm is None:
            try:
                from llama_cpp import Llama
                self._llm = Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_gpu_layers=self.n_gpu_layers,
                    verbose=False,
                    **self.kwargs,
                )
                self._vocab_size = self._llm.n_vocab()
            except ImportError as e:
                raise ImportError(
                    "LlamaCppBackend requires 'llama-cpp-python'. "
                    "Install with: pip install llama-cpp-python"
                ) from e

    @property
    def vocab_size(self) -> int:
        return self._vocab_size

    def forward(
        self,
        input_ids: List[int],
        block_tables: Optional[List[List[int]]] = None,
        is_prefill: bool = False,
    ) -> List[float]:
        self._ensure_loaded()
        self._llm.reset()
        self._llm.eval(input_ids)
        logits = self._llm.scores[-1, :self._vocab_size]
        return logits.tolist()

    def tokenize(self, text: str) -> List[int]:
        self._ensure_loaded()
        return self._llm.tokenize(text.encode("utf-8"))

    def detokenize(self, token_ids: List[int]) -> str:
        self._ensure_loaded()
        return self._llm.detokenize(token_ids).decode("utf-8", errors="replace")

