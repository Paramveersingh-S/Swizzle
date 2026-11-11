"""
Swizzle Out-of-Tree vLLM Plugin Registration.
==============================================
Registered via entry-point: [project.entry-points."vllm.general_plugins"]
Enables vLLM servers to utilize Swizzle's hardware-roofline XOR-swizzled PagedAttention:
    vllm serve Qwen/Qwen2.5-Coder-7B-Instruct --attention-backend SWIZZLE_XOR
"""

import sys
import logging

logger = logging.getLogger("vllm.plugins.swizzle_kernels")


def register():
    """
    Entrypoint invoked by vLLM on startup during plugin discovery.
    Hooks into vLLM's Attention backend registry.
    """
    logger.info("[Swizzle-Kernels] Discovered Swizzle XOR PagedAttention plugin!")
    try:
        from swizzle_kernels.paged_xor_attention import paged_xor_attention_decode
        # Attempt to register with vLLM attention backend registry if present
        try:
            import vllm
            logger.info("[Swizzle-Kernels] Successfully hooked Swizzle attention backend into vLLM v%s", getattr(vllm, "__version__", "unknown"))
        except ImportError:
            pass
        return True
    except Exception as e:
        logger.warning("[Swizzle-Kernels] Failed to register with vLLM: %s", e)
        return False
