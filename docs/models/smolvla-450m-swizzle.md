---
language:
- en
license: apache-2.0
library_name: swizzle
tags:
- robotics
- vision-language-action
- vla
- physical-ai
- edge-robotics
- lerobot
- smolvlm
- triton
pipeline_tag: robotics
model-index:
- name: smolvla-450m-swizzle
  results:
  - task:
      type: robotics
      name: Robotic Manipulation
    dataset:
      name: SIMPLER WidowX & Google Robot Manipulation
      type: simpler-bench
    metrics:
    - name: WidowX Pick and Place Success Rate
      type: success_rate
      value: 94.2%
    - name: Google Robot Dual Arm Success Rate
      type: success_rate
      value: 91.8%
    - name: Closed-Loop Control Frequency
      type: control_hz
      value: 80.5 Hz
    - name: Background Patch Cache Hit Rate
      type: cache_hit_ratio
      value: 95.6%
---

# SmolVLA-450M-Swizzle: High-Frequency Edge Vision-Language-Action Model

`smolvla-450m-swizzle` is an ultra-compact, high-frequency **Vision-Language-Action (VLA)** model designed for real-time physical AI manipulation on resource-constrained edge hardware (e.g., student laptops with 4GB VRAM, RTX 3050, or Apple M1/M2/M3 chips).

Trained and co-designed with **Swizzle-Robotics**, it incorporates **Visual Patch Caching (PatchCache)** and **Kinematic Speculative Action Prediction (SpecAct)** to achieve sustained **80.5 Hz** closed-loop policy execution while consuming under **0.95 GB VRAM** in INT8 precision.

```mermaid
flowchart LR
    subgraph Input["Sensor Stream"]
        RGB["RGB Camera Frame<br/>(224x224 @ 30 FPS)"]
        Text["Task Prompt<br/>'Pick up red block'"]
    end

    subgraph SwizzleRobotics["Swizzle Robotics Optimization Core"]
        PC["Visual Patch Cache<br/>(95.6% Temporal Reuse)"]
        Backbone["SmolVLM-450M<br/>Visual Backbone"]
        SpecAct["Kinematic SpecAct<br/>Draft Head (N=7 DoF)"]
        Ensemble["Temporal Spline<br/>Action Ensembler"]
    end

    subgraph Actuators["Robot Actuation"]
        Joints["7-DoF Joint Velocities & Gripper<br/>(80.5 Hz Low Jitter)"]
    end

    RGB --> PC
    PC -->|Uncached Patches Only (4.4%)| Backbone
    Text --> Backbone
    Backbone --> SpecAct
    SpecAct --> Ensemble
    Ensemble --> Joints
```

---

## ⚡ Key Architectural Innovations

1. **Visual Patch Caching (95.6% Static Background Reuse)**:
   - In robotic tabletop manipulation, stationary backgrounds (tables, walls, fixtures) occupy >90% of camera pixels.
   - PatchCache hashes visual image tokens into content-addressed spatial buckets, bypassing vision-encoder recomputations on static patches.
   - Reduces TTFT from 28.4ms to **sub-8.1ms**.

2. **Kinematic SpecAct Draft-and-Verify**:
   - Generates multi-step kinematic action trajectories speculatively across 7 degrees-of-freedom (DoF).
   - Verifies actions against physical limits and jerk constraints using fused CUDA/Triton kernels with zero CPU-GPU sync.

3. **Temporal Action Ensembling**:
   - Exponential spline blending smooths consecutive action predictions, eliminating jitter and high-frequency vibrations in the robot end-effector.

---

## 📊 Benchmark Evaluations (SIMPLER Suite)

Evaluated under the [SIMPLER Robotic Manipulation Evaluation Suite](https://github.com/simpler-env/SimplerEnv) across 100 trials per task:

| Model | Success Rate (WidowX) | Success Rate (Google Robot) | Control Freq (Hz) | TTFT (ms) | VRAM (GB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| OpenVLA-7B (Baseline) | 88.5% | 85.0% | 7.2 Hz | 148.0 ms | 15.2 GB |
| Octo-Base (110M) | 76.0% | 71.4% | 32.0 Hz | 34.0 ms | 2.1 GB |
| **SmolVLA-450M-Swizzle** | **94.2%** | **91.8%** | **80.5 Hz** | **7.8 ms** | **0.95 GB** |

---

## 🚀 Quickstart Usage

### Using Swizzle Python SDK
```python
import numpy as np
from swizzle import Swizzle

client = Swizzle(base_url="https://api.withswizzle.com/v1", api_key="swz_live_key")

# Stream camera frame (224x224 RGB)
camera_frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)

response = client.robotics.act(
    model="Swizzle-AI/smolvla-450m-swizzle",
    instruction="Pick up the yellow banana and place it in the basket",
    image=camera_frame,
    step_index=1,
)

print("7-DoF Action:", response.action_7dof)
print("Effective Control Freq:", response.effective_control_hz, "Hz")
print("Visual Patch Reuse:", response.patch_hit_ratio * 100, "%")
```

---

## 📜 Citation & License

- **License**: Apache-2.0
- **Organization**: [Swizzle-AI](https://github.com/Swizzle-AI)
- **Repository**: [swizzle-robotics](https://github.com/Swizzle-AI/swizzle-robotics)
