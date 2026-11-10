from __future__ import annotations
import math
from typing import Any, List, Optional, Sequence
from ..types import PatchCacheDecision

def extract_patch_intensities_from_frame(frame: Any, grid_size: int = 14) -> List[float]:
    """
    Extracts normalized [0.0, 1.0] patch intensities from a camera / webcam frame.
    Supports:
    - 1D sequence of float patch intensities
    - numpy ndarray (cv2.VideoCapture frames, shape (H, W, 3) BGR/RGB or (H, W))
    - PIL.Image.Image
    """
    total = grid_size * grid_size
    if isinstance(frame, (list, tuple)) and frame and isinstance(frame[0], (int, float)):
        intensities = [float(x) for x in frame]
        if len(intensities) < total:
            intensities.extend([0.0] * (total - len(intensities)))
        return intensities[:total]

    if hasattr(frame, "convert") and hasattr(frame, "size"):
        gray_img = frame.convert("L").resize((grid_size, grid_size))
        pixels = list(gray_img.getdata())
        return [round(p / 255.0, 4) for p in pixels]

    if hasattr(frame, "shape") and hasattr(frame, "ndim"):
        try:
            import cv2
            if frame.ndim == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            elif frame.ndim == 2:
                gray = frame
            else:
                gray = frame.squeeze()
            resized = cv2.resize(gray, (grid_size, grid_size), interpolation=cv2.INTER_AREA)
            val = resized.astype(float)
            if val.max() > 1.0:
                val = val / 255.0
            return [round(float(x), 4) for x in val.flatten()]
        except Exception:
            pass

        try:
            import numpy as np
            arr = np.asarray(frame)
            if arr.ndim == 3:
                gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
            elif arr.ndim == 2:
                gray = arr.astype(float)
            else:
                gray = arr.squeeze().astype(float)

            H, W = gray.shape
            ch, cw = max(1, H // grid_size), max(1, W // grid_size)
            cropped = gray[: ch * grid_size, : cw * grid_size]
            reshaped = cropped.reshape(grid_size, ch, grid_size, cw).mean(axis=(1, 3))
            max_v = float(np.max(reshaped))
            if max_v > 1.0:
                reshaped = reshaped / 255.0
            return [round(float(x), 4) for x in reshaped.flatten()]
        except Exception:
            pass

    raise TypeError(
        f"Cannot extract {grid_size}x{grid_size} patch intensities from frame of type {type(frame)}. "
        "Provide a numpy ndarray, PIL Image, or Sequence[float]."
    )

class PatchCacheFilter:
    """
    Swizzle-PatchCache: Spatio-Temporal ViT Patch Delta & KV Reuse Filter.
    Tracks 14x14 (196) or 16x16 (256) camera patch intensities across frames and skips
    ViT encoding + VLM prefill for unchanged static background patches.
    """

    def __init__(self, grid_size: int = 14, delta_threshold: float = 0.025):
        self.grid_size = grid_size
        self.delta_threshold = delta_threshold
        self.frame_index = 0
        self._ref_intensities: Optional[List[float]] = None

    def evaluate(self, patch_intensities: Sequence[float]) -> PatchCacheDecision:
        self.frame_index += 1
        intensities = [float(x) for x in patch_intensities]
        total = len(intensities)

        if self._ref_intensities is None or len(self._ref_intensities) != total:
            self._ref_intensities = list(intensities)
            reuse_mask = [False] * total
            reused = 0
        else:
            reuse_mask = []
            reused = 0
            for idx, curr in enumerate(intensities):
                prev = self._ref_intensities[idx]
                if abs(curr - prev) <= self.delta_threshold:
                    reuse_mask.append(True)
                    reused += 1
                else:
                    reuse_mask.append(False)
                    self._ref_intensities[idx] = curr

        recomputed = total - reused
        hit_ratio = reused / max(1, total)

        # Baseline: 42ms for 224x224 ViT+VLM prefill, 6.5ms fixed prompt overhead
        baseline_ms = 42.0
        fixed_ms = 6.5
        swizzle_ms = fixed_ms + (baseline_ms - fixed_ms) * (recomputed / max(1.0, float(total)))
        speedup = baseline_ms / max(1.0, swizzle_ms)

        return PatchCacheDecision(
            frame_index=self.frame_index,
            total_patches=total,
            reused_patches=reused,
            recomputed_patches=recomputed,
            patch_hit_ratio=round(hit_ratio, 4),
            prefill_speedup=round(speedup, 2),
            baseline_prefill_ms=baseline_ms,
            swizzle_prefill_ms=round(swizzle_ms, 2),
            reuse_mask=reuse_mask,
        )
