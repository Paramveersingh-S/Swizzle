"""
Swizzle Python SDK
~~~~~~~~~~~~~~~~~~
Ultra-low latency, prefix-cached, speculative LLM inference client.
"""

from .client import Swizzle, AsyncSwizzle
from .exceptions import SwizzleError, AuthenticationError, RateLimitError, WorkerUnavailableError
from .types import SwizzleTelemetry, ChatCompletion, ChatCompletionChunk

__version__ = "0.1.0"
__all__ = [
    "Swizzle",
    "AsyncSwizzle",
    "SwizzleError",
    "AuthenticationError",
    "RateLimitError",
    "WorkerUnavailableError",
    "SwizzleTelemetry",
    "ChatCompletion",
    "ChatCompletionChunk",
]

