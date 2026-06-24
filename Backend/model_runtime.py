from fall_model import unload_fall_model
from fire_smoke_model import unload_fire_model
from pose_model import unload_pose_model
from ppe_model import unload_ppe_model


def sleep_model(model_type: str) -> None:
    if model_type == "ppe":
        unload_ppe_model()
    elif model_type == "fire-smoke":
        unload_fire_model()
    elif model_type == "fall":
        unload_fall_model()
    elif model_type == "pose":
        unload_pose_model()


def sleep_all_models() -> None:
    unload_ppe_model()
    unload_fire_model()
    unload_fall_model()
    unload_pose_model()
