# Swizzle (`withswizzle.com`)

**Speed-of-light inference at the hardware roofline.**
Named after **XOR shared-memory swizzling**—the hardware technique that eliminates GPU SRAM bank conflicts so Tensor and Matrix Cores execute at 100% memory and compute utilization.

---

## Architecture & Core Wedges

Swizzle is an asymmetric inference engine and edge control plane built for **real-time voice agents**, **100K+ context coding agents**, and **autonomous cybersecurity / red-team workflows**.

```
[Coding / Voice / AppSec Agents]
       │  HTTP/2 + QUIC (300s Keep-Alive, Zero TLS Re-Handshake)
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Swizzle Edge Control Plane (gateway/)                                │
│  • OpenAI (/v1/chat/completions) & Anthropic (/v1/messages) Native   │
│  • Atomic Valkey Prefix-Cache Ledger (90% cached token discount)     │
│  • Immediate First-Delta TTFT Streamer (<38ms cached prefill TTFT)   │
│  • Zero-Data-Retention (ZDR) Ephemeral Memory Attestation (/cyber)   │
└──────────────────────────────────────────────────────────────────────┘
       │
       ├──► [Wedge 1: Coding & Speculative Repo Engine]
       │     • Qwen3.6-35B-A3B-FP8 & DeepSeek-V4.1-Flash (1M Context)
       │     • Prompt-Lookup Speculative Decoding (PLD) + LMCache Offload
       │     • 440+ tok/s output on code diffs, <38ms TTFT on 100K repos
       │
       ├──► [Wedge 2: /cyber Offensive & Defensive AppSec Engine]
       │     • DeepSeek-V4.1-Flash-Abliterated & Qwen3.6-Cyber
       │     • Zero false-positive refusals on exploit analysis & WAF rules
       │     • Constrained SARIF / Unified-Diff grammar decoding
       │
       └──► [Wedge 3: Zero-Hop Voice-to-Voice Pipeline]
             • Gemma-4-31B (TPU v5e Megakernel) + In-Memory Diffusion TTS
             • Shared ring-buffer coupling (0ms LLM→TTS network serialization)
```

---

## Live Endpoint Benchmarks

| Model ID | Hardware Target | Cached TTFT | Uncached TTFT | Output Speed | Input / Cached / Output (per 1M) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `swizzle/qwen3.6-35b-a3b-fp8` | 1× AMD MI300X (192GB HBM3, `TP=1`) | **34 ms** | 72 ms | **465 tok/s** | `$0.20` / `$0.02` / `$0.80` |
| `swizzle/gemma-4-31b-it` | TPU v5e-8 Persistent Megakernel | **38 ms** | 76 ms | **138 tok/s** | `$0.25` / `$0.025` / `$0.75` |
| `swizzle/deepseek-v4.1-flash-1017` | 8× MI300X (`EP=8`, 1M Context) | **42 ms** | 105 ms | **390 tok/s** | `$0.25` / `$0.025` / `$1.00` |
| `swizzle/deepseek-v4.1-flash-abliterated` | 8× MI300X (ZDR `/cyber` Enclave) | **42 ms** | 105 ms | **390 tok/s** | `$0.25` / `$0.025` / `$1.00` |
| `swizzle/sonar-tts-fast` | H100 Custom PTX Fused Vocoder | **68 ms** (TTFA) | 68 ms | **34× RT** | `$4.00` / 1M chars |

---

## Repository Layout

- [`gateway/`](./gateway) — Go `/v1` Edge Control Plane supporting OpenAI Chat Completions, Anthropic Messages API (native Claude Code drop-in), atomic prefix-cache billing, and real-time latency telemetry headers (`X-Swizzle-TTFT-Ms`, `X-Swizzle-Cache-Hit-Ratio`, `X-Swizzle-Speculative-Accept-Rate`).
- [`web/`](./web) — Roofline-first technical web platform (`withswizzle.com`), interactive latency/cost comparator, `/cyber` AppSec portal, `/agents/quickstart.md` agent onboarding spec, and deep kernel engineering worklogs.

