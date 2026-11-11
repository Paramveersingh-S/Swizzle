from .base import BaseVLAPolicy, BaseWorldModel
from .cosmos_wm import CosmosWorldModel
from .gr00t_policy import Gr00tPolicy
from .smol_vla import SmolVLAPolicy
from .openvla import OpenVLAPolicy
from .pi0_flow import Pi0Policy
from .vjepa_wm import VJEPAWorldModel
from .lerobot_policy import LeRobotPolicyWrapper

MODEL_REGISTRY = {
    "nvidia/cosmos-predict-mini": CosmosWorldModel,
    "nvidia/gr00t-manipulator-v1": Gr00tPolicy,
    "lerobot/smolvla-450m": SmolVLAPolicy,
    "lerobot/act_aloha_sim_transfer_cube": LeRobotPolicyWrapper,
    "openvla/openvla-7b-swizzle": OpenVLAPolicy,
    "physical-intelligence/pi0-fast": Pi0Policy,
    "meta/vjepa2-latent-mpc": VJEPAWorldModel,
    "meta/dino-wm-latent": VJEPAWorldModel,
}

def get_policy(model_name: str) -> BaseVLAPolicy:
    """Factory helper to load VLA policy by name."""
    cls = MODEL_REGISTRY.get(model_name)
    if cls and issubclass(cls, BaseVLAPolicy):
        return cls(model_name=model_name)
    return SmolVLAPolicy(model_name="lerobot/smolvla-450m")

def get_world_model(model_name: str) -> BaseWorldModel:
    """Factory helper to load World Model by name."""
    cls = MODEL_REGISTRY.get(model_name)
    if cls and issubclass(cls, BaseWorldModel):
        return cls(model_name=model_name)
    return CosmosWorldModel(model_name="nvidia/cosmos-predict-mini")

__all__ = [
    "BaseVLAPolicy",
    "BaseWorldModel",
    "CosmosWorldModel",
    "Gr00tPolicy",
    "SmolVLAPolicy",
    "OpenVLAPolicy",
    "Pi0Policy",
    "VJEPAWorldModel",
    "LeRobotPolicyWrapper",
    "MODEL_REGISTRY",
    "get_policy",
    "get_world_model",
]
