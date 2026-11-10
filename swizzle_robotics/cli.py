from __future__ import annotations
import argparse
import sys
from .hardware import HardwareDetector
from .models import get_policy, get_world_model, MODEL_REGISTRY
from .servoing import VisualServoingLoop
from .core.camera import LiveCamera, MockCamera
from .server import run_server

def main():
    parser = argparse.ArgumentParser(
        prog="swizzle-robotics",
        description="Swizzle Robotics: 80.5 Hz Visual Servoing, Latent World Models & Edge Accelerators."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: detect
    subparsers.add_parser("detect", help="Detect local GPU hardware and recommend models")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run closed-loop visual servoing")
    run_parser.add_argument("--model", type=str, default="lerobot/smolvla-450m", help="VLA model identifier")
    run_parser.add_argument("--steps", type=int, default=30, help="Number of control steps to execute")
    run_parser.add_argument("--camera", type=int, default=0, help="Camera device index")
    run_parser.add_argument("--mock", action="store_true", help="Force synthetic mock camera")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Launch Swizzle Robotics REST API server")
    serve_parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    serve_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind")

    args = parser.parse_args()

    if args.command == "detect" or not args.command:
        profile = HardwareDetector.detect()
        print("=" * 60)
        print("SWIZZLE ROBOTICS HARDWARE & MODEL PROFILE")
        print("=" * 60)
        print(f"Device Type:           {profile.device_type.upper()}")
        print(f"Device Name:           {profile.device_name}")
        print(f"Detected VRAM:         {profile.vram_gb:.2f} GB")
        print(f"Recommended VLA:       {profile.recommended_vla}")
        print(f"Recommended World Mod: {profile.recommended_world_model}")
        print(f"Quantization Target:   {profile.recommended_quantization}")
        print(f"Needs Colab Tunnel:    {'YES (7B requires tunnel)' if profile.needs_colab_tunnel_for_7b else 'NO (Fully local)'}")
        print("=" * 60)

    elif args.command == "serve":
        run_server(port=args.port, host=args.host)

    elif args.command == "run":
        print(f"Initializing Swizzle Visual Servoing with policy '{args.model}'...")
        policy = get_policy(args.model)
        camera = MockCamera() if args.mock else LiveCamera(camera_id=args.camera)
        loop = VisualServoingLoop(policy=policy, camera=camera, target_hz=80.5)

        print(f"Executing {args.steps} closed-loop servoing steps:")
        print(f"{'Step':<6} | {'Hz':<8} | {'Latency':<10} | {'Patch Reuse':<12} | {'SpecAct':<8} | {'7-DoF Actuation [dx, dy, dz, ...]':<30}")
        print("-" * 85)

        for s in range(args.steps):
            telemetry = loop.step("Pick up target object")
            act_str = f"[{', '.join(f'{x:.2f}' for x in telemetry.action_7dof[:3])}, ...]"
            print(f"{telemetry.step:<6} | {telemetry.effective_hz:<8.1f} | {telemetry.dt_ms:<7.2f} ms | {telemetry.patch_hit_ratio * 100:<10.1f}% | {telemetry.spec_act_rate * 100:<6.0f}% | {act_str}")

if __name__ == "__main__":
    main()
