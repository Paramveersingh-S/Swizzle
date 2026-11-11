"""
Swizzle Continuous Batching Engine: Model Backends.
"""

from typing import Union, Optional
from .base import BaseModelBackend
from .simulation_backend import SimulationBackend

__all__ = [
    "BaseModelBackend",
    "SimulationBackend",
    "TransformersBackend",
    "VLLMBackend",
    "LlamaCppBackend",
    "create_backend",
]


def create_backend(
    model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
    backend_type: str = "auto",
    **kwargs,
) -> BaseModelBackend:
    """
    Factory function to instantiate the optimal model runner backend.

    backend_type options:
      - "auto": Checks if CUDA and transformers are available and can load weights; falls back to simulation.
      - "transformers": Hugging Face PyTorch AutoModelForCausalLM backend (for Colab Pro GPU).
      - "vllm": Remote or local vLLM API client backend.
      - "llamacpp": Local quantized GGUF inference backend.
      - "simulation": Zero-dependency deterministic simulation backend.
    """
    if backend_type == "transformers":
        from .transformers_backend import TransformersBackend
        return TransformersBackend(model_name_or_path=model_name, **kwargs)

    if backend_type == "vllm":
        from .vllm_backend import VLLMBackend
        return VLLMBackend(model_name=model_name, **kwargs)

    if backend_type == "llamacpp":
        from .llamacpp_backend import LlamaCppBackend
        return LlamaCppBackend(model_path=model_name, **kwargs)

    if backend_type == "simulation":
        vocab = 152064 if "qwen" in model_name.lower() else 128256
        return SimulationBackend(model_name=model_name, vocab_size=vocab)

    # "auto" resolution:
    if backend_type == "auto":
        try:
            import torch
            if torch.cuda.is_available() and kwargs.get("try_gpu", False):
                from .transformers_backend import TransformersBackend
                return TransformersBackend(model_name_or_path=model_name, **kwargs)
        except Exception:
            pass

    # Default fallback to simulation
    vocab = 152064 if "qwen" in model_name.lower() else 128256
    return SimulationBackend(model_name=model_name, vocab_size=vocab)
