"""
Tests for Swizzle Hugging Face LeRobot Integration.
===================================================
Validates SwizzleAcceleratedLeRobotPolicy wrapper, PatchCache token pruning,
telemetry gathering, and LeRobotPolicyWrapper action generation.
"""

import pytest
import numpy as np
from swizzle_robotics.lerobot_integration import (
    SwizzleAcceleratedLeRobotPolicy,
    wrap_lerobot_policy,
)
from swizzle_robotics.models.lerobot_policy import LeRobotPolicyWrapper
from swizzle_robotics.models import get_policy


class MockLeRobotACTPolicy:
    """Mock policy matching Hugging Face LeRobot ACTPolicy interface."""

    def __init__(self):
        self.step_count = 0

    def select_action(self, observation):
        self.step_count += 1
        # Returns 7-DoF action vector
        return np.array([0.05, -0.02, 0.01, 0.0, 0.0, 0.0, 1.0], dtype=np.float32)

    def reset(self):
        self.step_count = 0


def test_accelerated_lerobot_policy_wrapper():
    base_policy = MockLeRobotACTPolicy()
    accelerated = wrap_lerobot_policy(base_policy, grid_size=14, delta_threshold=0.03)

    # Frame 1: Static background frame
    frame1 = np.ones((112, 112, 3), dtype=np.uint8) * 128
    obs1 = {"pixels": frame1}

    act1 = accelerated.select_action(obs1)
    assert len(act1) == 7
    telemetry1 = accelerated.get_telemetry()
    assert telemetry1["patch_cache_active"] is True
    assert telemetry1["frame_index"] == 1
    assert telemetry1["recomputed_patches"] == 196
    assert telemetry1["patch_hit_ratio"] == 0.0

    # Frame 2: Identical frame (static background) -> PatchCache should hit ~100%
    obs2 = {"pixels": frame1.copy()}
    act2 = accelerated.select_action(obs2)
    assert len(act2) == 7
    telemetry2 = accelerated.get_telemetry()
    assert telemetry2["frame_index"] == 2
    assert telemetry2["reused_patches"] == 196
    assert telemetry2["patch_hit_ratio"] == 1.0
    assert telemetry2["prefill_speedup"] > 3.0


def test_lerobot_policy_wrapper_interface():
    policy = LeRobotPolicyWrapper(model_name="lerobot/act_aloha_sim_transfer_cube")
    assert policy.model_name == "lerobot/act_aloha_sim_transfer_cube"

    frame = np.zeros((112, 112, 3), dtype=np.uint8)
    chunk = policy.forward_action_chunk(frame, prompt="pick up the object", horizon=16)

    assert chunk.horizon == 16
    assert len(chunk.actions) == 16
    assert len(chunk.actions[0]) == 7
    assert chunk.actions[0][6] == 1.0  # Gripper closed on 'pick'


def test_factory_get_lerobot_policy():
    policy = get_policy("lerobot/act_aloha_sim_transfer_cube")
    assert isinstance(policy, LeRobotPolicyWrapper)
