"""
Test for Swizzle Live Smoke Test Protocol.
==========================================
Replicates scripts/swizzle_live_smoke_test.py end-to-end against the local
FastAPI continuous batching server to verify model probing, cold completion,
and warm streaming with telemetry headers.
"""

from fastapi.testclient import TestClient
from swizzle.api_server import app


def test_live_smoke_pipeline():
    client = TestClient(app)

    # 1. Probe Model Catalog
    models_res = client.get("/v1/models")
    assert models_res.status_code == 200
    models = models_res.json().get("data", [])
    assert len(models) >= 1
    assert any("Qwen" in m["id"] for m in models)

    # 2. Turn 1 (Cold Prompt)
    prompt_p1 = "package main\n\nimport \"net/http\"\n\nfunc HealthCheck(w http.ResponseWriter, r *http.Request) {\n"
    turn1_payload = {
        "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "messages": [
            {"role": "system", "content": "You are a high-performance Go coding agent."},
            {"role": "user", "content": f"Here is the service code:\n{prompt_p1}\nAdd a healthcheck route handler."},
        ],
        "stream": False,
        "max_tokens": 16,
    }

    t1_res = client.post("/v1/chat/completions", json=turn1_payload)
    assert t1_res.status_code == 200
    t1_data = t1_res.json()
    assert t1_data["object"] == "chat.completion"
    assert len(t1_data["choices"]) > 0
    assert t1_res.headers.get("x-swizzle-speculative-speedup") == "3.25x"
    assert "x-swizzle-ttft-ms" in t1_res.headers

    # 3. Turn 2 (Warm Prefix Streaming)
    turn2_payload = {
        "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "messages": [
            {"role": "system", "content": "You are a high-performance Go coding agent."},
            {"role": "user", "content": f"Here is the service code:\n{prompt_p1}\nAdd a healthcheck route handler."},
            {"role": "assistant", "content": t1_data["choices"][0]["message"]["content"]},
            {"role": "user", "content": "Now add Prometheus latency metrics."},
        ],
        "stream": True,
        "max_tokens": 16,
    }

    t2_res = client.post("/v1/chat/completions", json=turn2_payload)
    assert t2_res.status_code == 200
    assert t2_res.headers.get("x-swizzle-ast-reuse-pct") == "48.5%"
    chunks = [line for line in t2_res.text.split("\n") if line.startswith("data: ")]
    assert len(chunks) >= 2
    assert chunks[-1] == "data: [DONE]"
