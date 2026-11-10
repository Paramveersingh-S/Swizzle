"""
Tests for Swizzle Production API Server.
========================================
Validates OpenAI-compatible completions, SSE streaming, model listing,
and telemetry metrics against Swizzle LLMEngine.
"""

import pytest
from fastapi.testclient import TestClient
from swizzle.api_server import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["engine"] == "swizzle"
    assert data["version"] == "0.2.0"


def test_list_models(client):
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    models = [m["id"] for m in data["data"]]
    assert "Qwen/Qwen2.5-Coder-7B-Instruct" in models


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "step_counter" in data
    assert "prefix_cache_hit_ratio" in data
    assert "speculative_accepted_tokens" in data


def test_chat_completions_batch(client):
    payload = {
        "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "messages": [
            {"role": "system", "content": "You are a code optimizer."},
            {"role": "user", "content": "Optimize this matrix multiply function."},
        ],
        "max_tokens": 16,
        "stream": False,
    }
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"
    assert "choices" in data
    assert len(data["choices"]) > 0
    assert data["choices"][0]["finish_reason"] in ("length", "stop")
    assert data["usage"]["completion_tokens"] > 0


def test_chat_completions_streaming(client):
    payload = {
        "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "messages": [
            {"role": "user", "content": "Write a swizzle kernel test."},
        ],
        "max_tokens": 8,
        "stream": True,
    }
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    lines = [l for l in response.text.split("\n") if l.startswith("data: ")]
    assert len(lines) >= 2
    assert lines[-1] == "data: [DONE]"


def test_completions_endpoint(client):
    payload = {
        "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "prompt": "def fused_swizzle_gemm(",
        "max_tokens": 10,
        "stream": False,
    }
    response = client.post("/v1/completions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "text_completion"
    assert len(data["choices"]) > 0
    assert data["usage"]["completion_tokens"] > 0
