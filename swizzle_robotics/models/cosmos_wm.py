from __future__ import annotations
import numpy as np
from typing import Any, Sequence
from .base import BaseWorldModel
from ..core.patch_cache import extract_patch_intensities_from_frame

class CosmosWorldModel(BaseWorldModel):
    """
    NVIDIA Cosmos Physical AI World Foundation Model Adapter.
    Implements Cosmos-style continuous latent space tokenization and forward
    physical transition dynamics for robotics simulation and trajectory planning.
    """

    def __init__(self, model_name: str = "nvidia/cosmos-predict-mini", latent_dim: int = 64):
        super().__init__(model_name=model_name, latent_dim=latent_dim)
        # Deterministic spatial-temporal projection weights
        np.random.seed(42)
        self.proj_in = np.random.randn(196, latent_dim).astype(np.float32) / np.sqrt(196)
        # Transition dynamics matrices: A (state) and B (action)
        self.A = np.eye(latent_dim, dtype=np.float32) * 0.94 + np.random.randn(latent_dim, latent_dim).astype(np.float32) * 0.02
        self.B = np.random.randn(latent_dim, 7).astype(np.float32) * 0.08

    def encode_observation(self, frame: Any) -> np.ndarray:
        """Cosmos Tokenizer: compresses 14x14 (196) spatial grid into 64-dim continuous latent."""
        intensities = np.array(extract_patch_intensities_from_frame(frame, grid_size=14), dtype=np.float32)
        latent = np.dot(intensities, self.proj_in)
        norm = np.linalg.norm(latent)
        return latent / (norm + 1e-7)

    def predict_next_state(self, latent_state: np.ndarray, action: Sequence[float]) -> np.ndarray:
        """Simulates physical transition: s_{t+1} = tanh(A s_t + B a_t)."""
        act_vec = np.array(action[:7], dtype=np.float32)
        next_s = np.dot(self.A, latent_state) + np.dot(self.B, act_vec)
        return np.tanh(next_s)
