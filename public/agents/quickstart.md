# Swizzle Agent Onboarding (`withswizzle.com`)

You are configuring the user's project to run on **Swizzle** (`https://api.withswizzle.com/v1`), a hardware-roofline inference engine offering sub-38ms cached TTFT and 465+ tok/s output via distributed Valkey KV-cache persistence and Prompt-Lookup Speculative Decoding.

## 1. Endpoints & Model IDs
- **OpenAI / LiteLLM Compatible Base URL**: `https://api.withswizzle.com/v1`
- **Anthropic Messages API Base URL (Claude Code Native)**: `https://api.withswizzle.com`
- **Models**:
  - `swizzle/qwen3.6-35b-a3b-fp8` — 465 tok/s, 34ms cached TTFT on 1x AMD MI300X (`TP=1`), `$0.20/1M` input (`$0.02/1M` cached), `$0.80/1M` output.
  - `swizzle/gemma-4-31b-it` — 138 tok/s, 38ms cached TTFT on Google TPU v5e-8 persistent megakernel, `$0.25/1M` input (`$0.025/1M` cached).
  - `swizzle/deepseek-v4.1-flash-1017` — 1M context coding & reasoning engine, 390 tok/s, `$0.25/1M` input (`$0.025/1M` cached), `$1.00/1M` output.
  - `swizzle/deepseek-v4.1-flash-abliterated` — Zero-refusal Red/Blue-Team AppSec model with cryptographic Zero-Data-Retention (ZDR) RAM attestation.

## 2. Claude Code One-Liner
```bash
export ANTHROPIC_BASE_URL="https://api.withswizzle.com"
export ANTHROPIC_API_KEY="$SWIZZLE_API_KEY"
export ANTHROPIC_MODEL="swizzle/deepseek-v4.1-flash-1017"
claude
```

