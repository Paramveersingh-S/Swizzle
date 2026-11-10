import platform
import subprocess
from typing import Optional
from .types import StudentHardwareProfile

class HardwareDetector:
    """Detects student laptop/PC GPU capacity and recommends optimal VLA & World Model tiers."""

    @staticmethod
    def detect(override_vram_gb: Optional[float] = None) -> StudentHardwareProfile:
        device_type = "cpu"
        device_name = platform.processor() or "Laptop / PC CPU"
        vram_gb = 2.0

        if override_vram_gb is not None:
            vram_gb = float(override_vram_gb)
            device_type = "cuda" if vram_gb >= 3.5 else "cpu"
            device_name = f"Configured Student Hardware ({vram_gb:.1f} GB VRAM)"
        else:
            try:
                import torch
                if torch.cuda.is_available():
                    device_type = "cuda"
                    device_name = torch.cuda.get_device_name(0)
                    vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024.0 ** 3), 2)
            except Exception:
                pass

            if device_type == "cpu":
                try:
                    out = subprocess.check_output(
                        ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                        stderr=subprocess.DEVNULL,
                        timeout=1.5,
                        text=True,
                    ).strip()
                    if out:
                        first_line = out.splitlines()[0]
                        parts = [p.strip() for p in first_line.split(",")]
                        if len(parts) >= 2:
                            device_type = "cuda"
                            device_name = parts[0]
                            vram_gb = round(float(parts[1]) / 1024.0, 2)
                except Exception:
                    if platform.system() == "Darwin" and platform.machine() == "arm64":
                        device_type = "mps"
                        device_name = "Apple Silicon Unified GPU (MPS)"
                        vram_gb = 8.0

        if vram_gb < 3.0:
            rec_vla = "lerobot/smolvla-450m"
            rec_wm = "meta/dino-wm-latent"
            quant = "INT8 / FP16"
        elif vram_gb < 6.0:
            rec_vla = "lerobot/smolvla-450m"
            rec_wm = "nvidia/cosmos-predict-mini"
            quant = "INT8 AWQ"
        elif vram_gb < 10.0:
            rec_vla = "physical-intelligence/pi0-fast"
            rec_wm = "nvidia/cosmos-predict-mini"
            quant = "INT4 AWQ / FP8"
        else:
            rec_vla = "openvla/openvla-7b-swizzle"
            rec_wm = "nvidia/cosmos-predict-mini"
            quant = "INT4 / FP16"

        return StudentHardwareProfile(
            device_type=device_type,
            device_name=device_name,
            vram_gb=vram_gb,
            recommended_vla=rec_vla,
            recommended_world_model=rec_wm,
            recommended_quantization=quant,
            needs_colab_tunnel_for_7b=(vram_gb < 6.0),
        )
