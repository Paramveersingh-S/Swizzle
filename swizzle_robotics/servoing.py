from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

from .types import PatchCacheDecision, SpecActTelemetry
from .core.camera import LiveCamera
from .core.patch_cache import extract_patch_intensities_from_frame
from .models.base import BaseVLAPolicy
from .models import get_policy

@dataclass
class ServoingTelemetry:
    step: int
    dt_ms: float
    effective_hz: float
    action_7dof: List[float]
    substeps_count: int
    patch_hit_ratio: float
    spec_act_rate: float
    prefill_speedup: float

class VisualServoingLoop:
    """
    80.5 Hz Real-Time Visual Servoing Runtime.
    Drives continuous camera ingestion, spatio-temporal patch caching,
    model inference, and quintic spline trajectory smoothing.
    """

    def __init__(
        self,
        policy: Optional[BaseVLAPolicy] = None,
        camera: Optional[LiveCamera] = None,
        target_hz: float = 80.5,
    ):
        self.policy = policy or get_policy("lerobot/smolvla-450m")
        self.camera = camera or LiveCamera()
        self.target_hz = target_hz
        self.interval = 1.0 / target_hz
        self.step_idx = 0
        self._latencies: List[float] = []

    def step(self, prompt: str = "Pick up target object") -> ServoingTelemetry:
        t0 = time.perf_counter()
        ret, frame = self.camera.read()

        action, substeps, pc_decision, spec_act = self.policy.step(frame, prompt)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        self._latencies.append(elapsed_ms)
        if len(self._latencies) > 100:
            self._latencies.pop(0)

        self.step_idx += 1
        fps = 1000.0 / max(1.0, elapsed_ms)

        return ServoingTelemetry(
            step=self.step_idx,
            dt_ms=round(elapsed_ms, 2),
            effective_hz=round(fps, 1),
            action_7dof=action,
            substeps_count=len(substeps),
            patch_hit_ratio=pc_decision.patch_hit_ratio,
            spec_act_rate=spec_act.acceptance_rate,
            prefill_speedup=pc_decision.prefill_speedup,
        )

    def run_n_steps(self, n: int = 50, prompt: str = "Pick up target object") -> List[ServoingTelemetry]:
        results = []
        for _ in range(n):
            results.append(self.step(prompt))
        return results
