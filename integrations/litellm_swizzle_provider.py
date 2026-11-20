"""
Swizzle Custom Provider Adapter for LiteLLM & OpenAI-Compatible Agent Frameworks
==============================================================================
Designed for direct upstream contribution (`BerriAI/litellm`) and local agent usage:
- Routes requests to `swizzle-gateway` (`http://localhost:8080/v1`) or `swizzle-rt serve`
- Passes OpenAI `prediction` payloads cleanly to activate RAD-1 5.04x Fast-Apply edits
- Captures W3C `traceparent`, `X-Swizzle-Audit-Token`, `X-Swizzle-AST-Reuse-Pct`,
  `X-Swizzle-Saved-USD`, and `X-Swizzle-Secrets-Redacted` telemetry headers.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict, List, Optional


class SwizzleOpenAIProvider:
    """Zero-dependency OpenAI-compatible client & LiteLLM CustomLLM bridge."""

    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_s: float = 60.0,
    ):
        self.api_base = (api_base or os.getenv("SWIZZLE_BASE_URL") or "http://localhost:8080/v1").rstrip("/")
        self.api_key = api_key or os.getenv("SWIZZLE_API_KEY") or "sk-swizzle-dev-bypass-key"
        self.timeout_s = float(timeout_s)

    def completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        prediction_content: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        traceparent: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if prediction_content is not None:
            payload["prediction"] = {"type": "content", "content": prediction_content}
        if response_format is not None:
            payload["response_format"] = response_format

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        if traceparent:
            headers["traceparent"] = traceparent

        req = urllib.request.Request(
            f"{self.api_base}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            body["swizzle_headers"] = {
                "audit_token": resp.headers.get("X-Swizzle-Audit-Token", ""),
                "ttft_ms": resp.headers.get("X-Swizzle-TTFT-Ms", ""),
                "cache_hit_tokens": resp.headers.get("X-Swizzle-Cache-Hit-Tokens", "0"),
                "ast_reuse_pct": resp.headers.get("X-Swizzle-AST-Reuse-Pct", ""),
                "secrets_redacted": resp.headers.get("X-Swizzle-Secrets-Redacted", "0"),
                "saved_usd": resp.headers.get("X-Swizzle-Saved-USD", ""),
                "prediction_seed_tokens": resp.headers.get("X-Swizzle-Prediction-Seed-Tokens", "0"),
            }
            return body


try:
    from litellm import CustomLLM  # type: ignore

    class SwizzleLiteLLMHandler(CustomLLM):
        """Native LiteLLM CustomLLM handler for `model: swizzle/<model_id>`."""

        def completion(self, model: str, messages: list, **kwargs) -> Any:
            optional_params = kwargs.get("optional_params") or {}
            pred = optional_params.get("prediction") or kwargs.get("prediction")
            pred_content = pred.get("content") if isinstance(pred, dict) else None
            client = SwizzleOpenAIProvider(
                api_base=kwargs.get("api_base"),
                api_key=kwargs.get("api_key"),
            )
            return client.completion(
                model=model.removeprefix("swizzle/"),
                messages=messages,
                prediction_content=pred_content,
                response_format=optional_params.get("response_format"),
                temperature=float(optional_params.get("temperature", 0.0)),
                max_tokens=int(optional_params.get("max_tokens", 512)),
            )

except ImportError:
    SwizzleLiteLLMHandler = None  # LiteLLM optional at runtime
