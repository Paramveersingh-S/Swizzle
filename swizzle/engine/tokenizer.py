"""
Swizzle Continuous Batching Engine: Tokenizer Interface.

Provides unified encode / decode capabilities supporting Hugging Face AutoTokenizer,
tiktoken, and clean UTF-8 byte-level encoding fallback.
"""

from typing import List, Optional, Any


class SwizzleTokenizer:
    def __init__(self, model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct"):
        self.model_name = model_name
        self._tokenizer = None
        self._backend = "byte"

        # Try Hugging Face transformers AutoTokenizer (cached first, then network)
        try:
            from transformers import AutoTokenizer
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    local_files_only=True,
                )
            except Exception:
                self._tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                )
            self._backend = "hf"
            return
        except Exception:
            pass

        # Try tiktoken
        try:
            import tiktoken
            self._tokenizer = tiktoken.get_encoding("cl100k_base")
            self._backend = "tiktoken"
            return
        except Exception:
            pass

        # Fallback to UTF-8 Byte Offset
        self._backend = "byte"

    def encode(self, text: str) -> List[int]:
        if self._backend == "hf" and self._tokenizer is not None:
            return self._tokenizer.encode(text, add_special_tokens=False)
        elif self._backend == "tiktoken" and self._tokenizer is not None:
            return self._tokenizer.encode(text)
        else:
            return [int(b) + 1 for b in text.encode("utf-8")]

    def decode(self, token_ids: List[int]) -> str:
        if self._backend == "hf" and self._tokenizer is not None:
            return self._tokenizer.decode(token_ids, skip_special_tokens=True)
        elif self._backend == "tiktoken" and self._tokenizer is not None:
            return self._tokenizer.decode(token_ids)
        else:
            byte_vals = bytes([max(0, min(255, int(t) - 1)) for t in token_ids])
            return byte_vals.decode("utf-8", errors="replace")


_GLOBAL_TOKENIZER: Optional[SwizzleTokenizer] = None


def get_default_tokenizer(model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct") -> SwizzleTokenizer:
    global _GLOBAL_TOKENIZER
    if _GLOBAL_TOKENIZER is None or _GLOBAL_TOKENIZER.model_name != model_name:
        _GLOBAL_TOKENIZER = SwizzleTokenizer(model_name)
    return _GLOBAL_TOKENIZER
