# Swizzle Python SDK (`swizzle-ai`)

The official Python client for **Swizzle**: the high-performance inference engine built for autonomous coding agents with **sub-40ms cached TTFT**, **speculative decoding**, and **AST-diff virtual prefix caching**.

---

## ⚡ Installation

```bash
pip install swizzle-ai
```

Or install locally in editable mode:
```bash
pip install -e sdk/python
```

---

## 🚀 Quickstart

### 1. Basic Chat Completion with Real-Time Telemetry

```python
from swizzle import Swizzle

client = Swizzle(api_key="swz_live_free_tier")

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-Coder-7B-Instruct",
    messages=[
        {"role": "system", "content": "You are a code agent with prefix cache awareness."},
        {"role": "user", "content": "Write an XOR shared memory swizzle kernel in CUDA"}
    ]
)

print(response.choices[0].message.content)

# Access hardware-roofline telemetry returned by Swizzle
print(f"TTFT: {response.telemetry.ttft_ms} ms")
print(f"Prefix Cache Hit: {response.telemetry.cache_hit_tokens} tokens")
print(f"Speculative Speedup: {response.telemetry.speculative_speedup}")
print(f"AST-Tree Reuse: {response.telemetry.ast_reuse_pct}")
print(f"PD Disaggregation: {response.telemetry.pd_mode}")
```

---

### 2. Low-Latency Streaming

```python
from swizzle import Swizzle

client = Swizzle(api_key="swz_live_free_tier")

stream = client.chat.completions.create(
    model="Qwen/Qwen2.5-Coder-7B-Instruct",
    messages=[{"role": "user", "content": "Refactor this HTTP handler into Go"}],
    stream=True
)

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)

# Telemetry is attached to chunks as headers arrive:
print(f"\nSpeculative Engine: {chunk.telemetry.speculative_engine}")
```

---

### 3. Asynchronous Client (`AsyncSwizzle`)

```python
import asyncio
from swizzle import AsyncSwizzle

async def main():
    async with AsyncSwizzle(api_key="swz_live_free_tier") as client:
        response = await client.chat.completions.create(
            model="Qwen/Qwen2.5-Coder-7B-Instruct",
            messages=[{"role": "user", "content": "Benchmark matrix multiplication in Python"}]
        )
        print(response.choices[0].message.content)

asyncio.run(main())
```

---

## 🛡️ Telemetry Properties

Every `response.telemetry` object exposes:
* `ttft_ms`: Exact Time-To-First-Token in milliseconds.
* `cache_hit_tokens`: Tokens loaded directly from GPU HBM prefix cache.
* `speculative_speedup`: Effective throughput acceleration factor (e.g. `2.76x`).
* `speculative_acceptance`: Percentage of candidate draft tokens accepted (e.g. `90.5%`).
* `ast_reuse_pct`: Non-linear AST block cache reuse percentage (e.g. `89.6%`).
* `pd_mode`: `Disaggregated (Prefill->Decode)` or `Colocated`.
* `worker_node`: Target accelerator node ID.
* `cost_usd` & `saved_usd`: Exact metered micro-dollar accounting.
