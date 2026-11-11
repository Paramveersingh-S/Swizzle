"""
Swizzle Continuous Batching Engine: Hugging Face Transformers Backend.

Executes authentic PyTorch causal language model forward passes on GPU/Colab Pro (A100/L4)
with support for FP16, BF16, AutoTokenizer, and genuine next-token prediction.
"""

from typing import List, Optional, Any
import numpy as np
from .base import BaseModelBackend


class TransformersBackend(BaseModelBackend):
    def __init__(
        self,
        model_name_or_path: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
        device: str = "auto",
        torch_dtype: str = "auto",
        trust_remote_code: bool = True,
    ):
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as e:
            raise ImportError(
                "TransformersBackend requires 'torch' and 'transformers'. "
                "Install them with: pip install torch transformers accelerate"
            ) from e

        self.model_name = model_name_or_path

        # Device selection
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Dtype selection
        if torch_dtype == "auto":
            dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else (
                torch.float16 if torch.cuda.is_available() else torch.float32
            )
        elif torch_dtype in ("bfloat16", "bf16"):
            dtype = torch.bfloat16
        elif torch_dtype in ("float16", "fp16"):
            dtype = torch.float16
        else:
            dtype = torch.float32

        # Initialize Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path,
            trust_remote_code=trust_remote_code,
        )
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        # Initialize Model
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            torch_dtype=dtype,
            device_map=self.device if self.device != "cpu" else None,
            trust_remote_code=trust_remote_code,
        )
        if self.device == "cpu":
            self.model.to("cpu")
        self.model.eval()

        self._vocab_size = self.model.config.vocab_size

    @property
    def vocab_size(self) -> int:
        return self._vocab_size

    def forward(
        self,
        input_ids: List[int],
        block_tables: Optional[List[List[int]]] = None,
        is_prefill: bool = False,
    ) -> List[float]:
        import torch

        if not input_ids:
            input_ids = [self.tokenizer.eos_token_id or 0]

        tensor_ids = torch.tensor([input_ids], dtype=torch.long, device=self.device)

        with torch.no_grad():
            outputs = self.model(input_ids=tensor_ids, use_cache=False)
            # Take logits for the last token position
            next_token_logits = outputs.logits[0, -1, :].cpu().to(torch.float32).numpy()

        return next_token_logits.tolist()

    def tokenize(self, text: str) -> List[int]:
        return self.tokenizer.encode(text, add_special_tokens=False)

    def detokenize(self, token_ids: List[int]) -> str:
        return self.tokenizer.decode(token_ids, skip_special_tokens=True)
