---
title: Swizzle 24/7 Inference Worker
emoji: ⚡
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# ⚡ Swizzle 24/7 Cloud Inference Worker

Always-on, serverless inference worker for the **Swizzle-AI** ecosystem (`https://swizzle-ten.vercel.app/`), powered by Hugging Face Spaces.

## Capabilities
- OpenAI-compatible `/v1/chat/completions` and `/v1/models`
- Real-time Server-Sent Events (SSE) token streaming
- Spatio-temporal PatchCache and AST-diff virtual prefix caching telemetry
- Free ZeroGPU (NVIDIA A100 dynamic allocation) support
- Zero laptop dependency — runs 24/7 in the cloud

## Connect to Vercel
In your Vercel Project Settings for `swizzle-ten`:
- **`SWIZZLE_UPSTREAM_URL`** = `https://<YOUR_HF_USERNAME>-<SPACE_NAME>.hf.space`
