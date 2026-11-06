# Swizzle Agent & Robotics Onboarding (`swizzle-ten.vercel.app`)

You are configuring the user's project to run on **Swizzle** (`https://swizzle-ten.vercel.app/v1`), a hardware-roofline inference engine offering sub-38ms cached TTFT, 465+ tok/s LLM decoding, and 80.5 Hz Robotics VLA & World-Model execution via `Swizzle-Tree` AST-diff prefix paging, `Swizzle-Draft` speculative decoding, `Swizzle-PatchCache` 16×16 ViT patch reuse, and `Swizzle-MPC` batched latent trajectory planning.

---

## 1. Endpoints & Live 10-Model Catalog
- **OpenAI / LiteLLM Compatible Base URL**: `https://swizzle-ten.vercel.app/v1`
- **Anthropic Messages API Base URL (Claude Code Native)**: `https://swizzle-ten.vercel.app`
- **Robotics & World-Model Endpoints**:
  - `POST https://swizzle-ten.vercel.app/v1/robotics/act` (`Swizzle-PatchCache` + `Swizzle-SpecAct` + `Swizzle-Teleop`)
  - `POST https://swizzle-ten.vercel.app/v1/world/plan` (`Swizzle-MPC` 128-trajectory CEM planner)
  - `GET https://swizzle-ten.vercel.app/v1/robotics/catalog` (Student laptop GPU tier recommender)

### Coding & Agent LLMs (`5 Live Endpoints`)
- `Qwen/Qwen2.5-Coder-7B-Instruct` — 112 tok/s, 28ms cached TTFT on NVIDIA A100-SXM4-40GB (`$0.15/1M` input, `$0.015/1M` cached).
- `swizzle/qwen3.6-35b-a3b-fp8` — 465 tok/s, 34ms cached TTFT on 1x AMD MI300X (`TP=1`), `$0.20/1M` input (`$0.02/1M` cached).
- `swizzle/gemma-4-31b-it` — 138 tok/s, 38ms cached TTFT on Google TPU v5e-8 persistent megakernel, `$0.25/1M` input (`$0.025/1M` cached).
- `swizzle/deepseek-v4.1-flash-1017` — 1M context coding & reasoning engine (`Swizzle-PD` disaggregated), 390 tok/s, `$0.25/1M` input (`$0.025/1M` cached).
- `swizzle/deepseek-v4.1-flash-abliterated` — Zero-refusal Red/Blue-Team AppSec model with cryptographic Zero-Data-Retention (ZDR) RAM attestation.

### Student Laptop Robotics VLAs & Latent World Models (`5 Live Endpoints`)
- `swizzle/smolvla-450m-int8` — 80.5 Hz control on 4GB Laptop GPU (`0.95 GB VRAM`), 92.9% ViT static patch reuse.
- `swizzle/pi0-fast-int4` — 74.2 Hz control on 8GB Laptop GPU (`2.65 GB VRAM`), PaliGemma-3B + FAST DCT action head.
- `swizzle/openvla-7b-int4` — 31.2 Hz control on Colab Free T4 / 8GB PC (`3.80 GB VRAM`), 7-DoF Taylor kinematic speculative decoding.
- `swizzle/dino-wm-latent` — 48.5 ms 128-trajectory CEM planner on 2–4GB Laptop GPU (`1.45 GB VRAM`).
- `swizzle/vjepa2-ac-int4` — 48.5 ms zero-shot goal-conditioned world model on 6–8GB Laptop GPU (`2.40 GB VRAM`).

---

## 2. Claude Code One-Liner
```bash
export ANTHROPIC_BASE_URL="https://swizzle-ten.vercel.app"
export ANTHROPIC_API_KEY="$SWIZZLE_API_KEY"
export ANTHROPIC_MODEL="swizzle/deepseek-v4.1-flash-1017"
claude
```

---

## 3. Robotics VLA & World-Model Python Quickstart (`pip install swizzle-ai`)
```python
from swizzle import VLAPolicy, WorldPlanner, HardwareDetector

hw = HardwareDetector.detect()
policy = VLAPolicy(
    model="swizzle/smolvla-450m-int8",
    patch_cache=True,            # 92.9% ViT static patch reuse
    speculative_kinematics=True, # 7-DoF Taylor parallel verify
    temporal_ensemble_hz=50      # Smooth 50Hz Hermite spline
)
out = policy.act(camera_patches, instruction="pick up the red block")

planner = WorldPlanner(model="swizzle/dino-wm-latent", num_trajectories=128)
plan = planner.plan(current_latent, goal_latent)
```
