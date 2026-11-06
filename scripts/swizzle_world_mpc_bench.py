#!/usr/bin/env python3
"""
Swizzle World-Model MPC & Teleop Benchmark (`swizzle_world_mpc_bench.py`)
=========================================================================
Evaluates Swizzle-MPC (Batched Latent World-Model Cross-Entropy Method Planning)
across DINO-WM, V-JEPA 2-AC, DIAMOND, and DreamerV3, plus Swizzle-Teleop 50Hz
Temporal Action Ensembling under a 110ms Cloudflare Tunnel.
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk", "python"))

from swizzle import WorldPlanner, TemporalActionEnsembler, HardwareDetector


def main():
    print("==========================================================================")
    print("🌍 SWIZZLE WORLD-MODEL MPC & TELEOP BENCHMARK (Student Laptop Tiers)")
    print("==========================================================================")

    # 1. Student Hardware Tier Recommendations
    print("\n1️⃣  Student Laptop Hardware Tier Auto-Recommendations:")
    for vram in [2.0, 4.0, 8.0, 12.0]:
        prof = HardwareDetector.detect(override_vram_gb=vram)
        print(
            f"  • {vram:4.1f} GB VRAM -> VLA: {prof.recommended_vla:<25} | "
            f"World Model: {prof.recommended_world_model:<24} | Quant: {prof.recommended_quantization}"
        )

    # 2. World Model Batched CEM Trajectory Planning (N=128 trajectories, T=5 horizon, K=3 CEM iterations)
    print("\n2️⃣  Swizzle-MPC Batched Latent Rollout & CEM Planning (N=128, T=5, K=3):")
    curr_latent = [0.12, -0.24, 0.08, 0.0, 0.0, 0.0, 1.0] * 8  # 56-D latent slice
    goal_latent = [0.58, 0.22, 0.44, 0.12, -0.08, 0.0, 1.0] * 8

    models = [
        "swizzle/dreamerv3-rssm",
        "swizzle/dino-wm-latent",
        "swizzle/diamond-diffusion-wm",
        "swizzle/vjepa2-ac-int4",
    ]
    for m in models:
        planner = WorldPlanner(model=m, num_trajectories=128, horizon=5, cem_iterations=3)
        res = planner.plan(curr_latent, goal_latent)
        dist_reduction = (1.0 - res.final_predicted_distance / res.initial_latent_distance) * 100.0
        print(
            f"  • {m:<28} | VRAM: {res.vram_used_gb:4.2f} GB | "
            f"Latency: {res.swizzle_batched_ms:5.1f} ms (vs {res.unbatched_baseline_ms:5.1f} ms, {res.planning_speedup:.2f}x) | "
            f"Goal Error Cut: -{dist_reduction:.1f}%"
        )

    # 3. Swizzle-Teleop 50Hz Temporal Action Ensembling over 110ms Cloud Tunnel
    print("\n3️⃣  Swizzle-Teleop 50Hz Receding-Horizon Action Ensembling (110ms Tunnel RTT):")
    ensembler = TemporalActionEnsembler(decay_lambda=0.05)
    for step in range(4):
        chunk = [[0.10 + 0.02 * (step + h), -0.05, 0.20 + 0.01 * (step + h), 0, 0, 0, 1.0] for h in range(8)]
        act, substeps = ensembler.push_chunk(step, chunk)
        print(
            f"  • Chunk Step {step} | Ensembled X: {act[0]:.4f} | "
            f"50Hz Spline Substeps X: {[s[0] for s in substeps]}"
        )

    print("==========================================================================")


if __name__ == "__main__":
    main()
