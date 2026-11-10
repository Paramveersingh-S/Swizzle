from __future__ import annotations
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional
import numpy as np

from .types import StudentHardwareProfile
from .hardware import HardwareDetector
from .models import get_policy, get_world_model, MODEL_REGISTRY
from .core.camera import MockCamera
from .core.patch_cache import extract_patch_intensities_from_frame

class RoboticsAPIHandler(BaseHTTPRequestHandler):
    """Zero-dependency HTTP Handler for Swizzle Robotics VLA and World Model Serving."""

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json(200, {"status": "ok"})

    def do_GET(self):
        if self.path in ("/v1/robotics/models", "/v1/robotics/catalog"):
            profile = HardwareDetector.detect()
            models = [
                {
                    "id": "nvidia/cosmos-predict-mini",
                    "label": "NVIDIA Cosmos Predict (World Foundation Model)",
                    "type": "world-model",
                    "vram_req_gb": 4.0,
                    "target_hz": 60.0,
                    "description": "Spatial-temporal continuous tokenizer and latent physical rollout simulator."
                },
                {
                    "id": "nvidia/gr00t-manipulator-v1",
                    "label": "NVIDIA Project GR00T (Humanoid & Dual-Arm)",
                    "type": "vla",
                    "vram_req_gb": 6.0,
                    "target_hz": 50.0,
                    "description": "Generalist robot foundation model with bimanual 7-DoF action chunking."
                },
                {
                    "id": "lerobot/smolvla-450m",
                    "label": "Hugging Face LeRobot SmolVLA (450M)",
                    "type": "vla",
                    "vram_req_gb": 1.5,
                    "target_hz": 80.5,
                    "description": "Ultra-lightweight edge VLA running locally on consumer laptops and Mac M-series."
                },
                {
                    "id": "openvla/openvla-7b-swizzle",
                    "label": "OpenVLA 7B (Swizzle-SpecAct Accelerated)",
                    "type": "vla",
                    "vram_req_gb": 6.5,
                    "target_hz": 31.2,
                    "description": "7B VLA foundation model with 2nd-order Taylor kinematic speculation."
                },
                {
                    "id": "physical-intelligence/pi0-fast",
                    "label": "Physical Intelligence Pi0 (Flow-Matching)",
                    "type": "vla",
                    "vram_req_gb": 4.5,
                    "target_hz": 45.0,
                    "description": "Fast ODE vector field integration for multi-task robotic manipulation."
                },
                {
                    "id": "meta/vjepa2-latent-mpc",
                    "label": "Meta V-JEPA 2 / DINO-WM (Latent CEM)",
                    "type": "world-model",
                    "vram_req_gb": 2.5,
                    "target_hz": 80.0,
                    "description": "Action-conditional joint embedding predictive architecture with sub-50ms CEM planning."
                }
            ]
            self._send_json(200, {
                "hardware": {
                    "device_type": profile.device_type,
                    "device_name": profile.device_name,
                    "vram_gb": profile.vram_gb,
                    "recommended_vla": profile.recommended_vla,
                    "recommended_world_model": profile.recommended_world_model,
                    "recommended_quantization": profile.recommended_quantization,
                    "needs_colab_tunnel": profile.needs_colab_tunnel_for_7b
                },
                "models": models
            })
        elif self.path in ("/health", "/v1/health"):
            self._send_json(200, {"status": "healthy", "service": "swizzle-robotics", "time": time.time()})
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if self.path == "/v1/robotics/act":
            model_name = payload.get("model", "lerobot/smolvla-450m")
            prompt = payload.get("prompt", "Pick up target object")
            frame_data = payload.get("frame")
            if frame_data is None:
                # Use synthetic test frame
                cam = MockCamera()
                _, frame_data = cam.read()

            policy = get_policy(model_name)
            act, substeps, pc_decision, spec_act = policy.step(frame_data, prompt)
            self._send_json(200, {
                "model": model_name,
                "action_7dof": act,
                "substeps_count": len(substeps),
                "patch_cache": {
                    "reused_patches": pc_decision.reused_patches,
                    "total_patches": pc_decision.total_patches,
                    "hit_ratio": pc_decision.patch_hit_ratio,
                    "prefill_speedup": pc_decision.prefill_speedup,
                    "swizzle_prefill_ms": pc_decision.swizzle_prefill_ms
                },
                "spec_act": {
                    "acceptance_rate": spec_act.acceptance_rate,
                    "speedup": spec_act.decoding_speedup
                }
            })

        elif self.path == "/v1/world/plan":
            model_name = payload.get("model", "nvidia/cosmos-predict-mini")
            horizon = payload.get("horizon", 5)
            samples = payload.get("samples", 32)
            wm = get_world_model(model_name)

            cam = MockCamera()
            _, curr_frame = cam.read()
            cam.frame_idx = 10
            _, goal_frame = cam.read()

            best_act, full_traj, latency = wm.plan_cem(curr_frame, goal_frame, horizon=horizon, num_samples=samples)
            self._send_json(200, {
                "model": model_name,
                "horizon": horizon,
                "best_action": best_act,
                "planned_trajectory": full_traj,
                "planning_latency_ms": round(latency, 2),
                "samples_evaluated": samples
            })
        else:
            self._send_json(404, {"error": "Endpoint not found"})

def run_server(port: int = 8080, host: str = "0.0.0.0"):
    server = HTTPServer((host, port), RoboticsAPIHandler)
    print(f"🚀 Swizzle Robotics Server running at http://{host}:{port}")
    print(f"  - Model Catalog: http://{host}:{port}/v1/robotics/models")
    print(f"  - Action Endpoint: POST http://{host}:{port}/v1/robotics/act")
    print(f"  - World Model Planner: POST http://{host}:{port}/v1/world/plan")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
