"""
Swizzle Kernels: Hardware-Roofline Bitwise XOR Paged Attention & Megakernels.
"""

from .paged_xor_attention import paged_xor_attention_decode, swizzle_smem_index
from .vllm_plugin import register

__version__ = "0.2.0"

__all__ = [
    "paged_xor_attention_decode",
    "swizzle_smem_index",
    "register",
]
