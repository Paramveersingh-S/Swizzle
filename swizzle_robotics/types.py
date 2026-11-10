from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Dict, Any, Union

ACTION_VOCAB_BASE_TOKEN = 31744
ACTION_VOCAB_BINS = 256

def clamp_unit(val: float) -> float:
    """Clamps continuous actuation to [-1.0, 1.0]."""
    return max(-1.0, min(1.0, float(val)))

def quantize_action_to_token(val: float) -> int:
    """Discretizes continuous normalized action [-1.0, 1.0] to 256-bin VLA token."""
    v = clamp_unit(val)
    norm = (v + 1.0) * 0.5
    bin_idx = int(round(norm * (ACTION_VOCAB_BINS - 1)))
    bin_idx = max(0, min(ACTION_VOCAB_BINS - 1, bin_idx))
    return ACTION_VOCAB_BASE_TOKEN + bin_idx

def dequantize_token_to_action(token_id: int) -> float:
    """Converts a 256-bin discrete action token back to continuous [-1.0, 1.0]."""
    bin_idx = max(0, min(ACTION_VOCAB_BINS - 1, int(token_id) - ACTION_VOCAB_BASE_TOKEN))
    val = (bin_idx / float(ACTION_VOCAB_BINS - 1)) * 2.0 - 1.0
    return round(val, 4)

@dataclass
class ActionChunk:
    """Horizon H action chunk predicting multi-step continuous 7-DoF robot trajectory."""
    horizon: int
    actions: List[List[float]]  # Shape: (H, 7)
    confidence: float = 1.0
    source_model: str = "openvla-7b"

@dataclass
class PatchCacheDecision:
    """Per-frame spatio-temporal ViT patch reuse telemetry."""
    frame_index: int
    total_patches: int
    reused_patches: int
    recomputed_patches: int
    patch_hit_ratio: float
    prefill_speedup: float
    baseline_prefill_ms: float
    swizzle_prefill_ms: float
    reuse_mask: List[bool]

@dataclass
class SpecActTelemetry:
    """7-DoF kinematic speculative decoding telemetry."""
    drafted_action: List[float]
    verified_action: List[float]
    drafted_tokens: List[int]
    verified_tokens: List[int]
    accepted_dof_tokens: int
    acceptance_rate: float
    sequential_passes: int
    parallel_verify_passes: int
    decoding_speedup: float

@dataclass
class WorldRolloutResult:
    """Latent predictive world model forward simulation rollout."""
    initial_state_hash: str
    action_horizon: int
    predicted_latent_states: List[List[float]]
    trajectory_cost: float
    planning_latency_ms: float
    simulated_fps: float

@dataclass
class StudentHardwareProfile:
    """Detected hardware profile and optimal model recommendation."""
    device_type: str  # "cuda", "mps", "cpu"
    device_name: str
    vram_gb: float
    recommended_vla: str
    recommended_world_model: str
    recommended_quantization: str
    needs_colab_tunnel_for_7b: bool
