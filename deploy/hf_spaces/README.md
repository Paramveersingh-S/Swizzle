---
title: Swizzle 24/7 Inference Worker
emoji: ⚡
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.20.0
app_file: app.py
pinned: false
---

# ⚡ Swizzle 24/7 Cloud Inference Worker

Always-on, persistent inference worker for the **Swizzle-AI** ecosystem (`https://swizzle-ten.vercel.app/`), powered by Hugging Face Spaces (Free Tier).

## Capabilities
- OpenAI-compatible `/v1/chat/completions` and `/v1/models`
- Real-time Server-Sent Events (SSE) token streaming
- Spatio-temporal PatchCache and AST-diff virtual prefix caching telemetry
- Free 24/7 cloud runtime with zero laptop dependency

## Connect to Vercel
In your Vercel Project Settings for `swizzle-ten`:
- **`SWIZZLE_UPSTREAM_URL`** = `https://<YOUR_HF_USERNAME>-<SPACE_NAME>.hf.space`
