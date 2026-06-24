import os

import cv2
from ultralytics import YOLO


MODEL_PATHS = [
    os.path.join(os.path.dirname(__file__), "../Models/Pose/Pose/best.pt"),
    os.path.join(os.path.dirname(__file__), "../Models/Pose/Pose/last.pt"),
    os.path.join(
        os.path.dirname(__file__),
        "../Models/Fall_Detection/yolov8s-pose.pt",
    ),
]
_pose_model = None
_pose_model_path = None
_pose_model_error = None


def get_pose_model():
    global _pose_model, _pose_model_error, _pose_model_path
    if _pose_model is not None:
        return _pose_model

    _pose_model_error = None
    for model_path in MODEL_PATHS:
        if not os.path.exists(model_path):
            continue
        try:
            _pose_model = YOLO(model_path, task="pose")
            _pose_model_path = model_path
            return _pose_model
        except Exception as exc:  # noqa: BLE001
            _pose_model_error = str(exc)

    return _pose_model


def unload_pose_model() -> None:
    global _pose_model, _pose_model_path
    _pose_model = None
    _pose_model_path = None


def get_pose_model_error() -> str | None:
    return _pose_model_error


def get_pose_model_path() -> str | None:
    return _pose_model_path


def detect_pose(img):
    model = get_pose_model()
    if not model:
        return []

    results = model(
        img,
        imgsz=640,
        device="cuda" if cv2.cuda.getCudaEnabledDeviceCount() > 0 else "cpu",
    )

    detections = []
    for result in results:
        boxes = getattr(result, "boxes", None)
        kpts = getattr(result, "keypoints", None)
        if boxes is None:
            continue

        for idx, box in enumerate(boxes):
            keypoints = []
            if kpts is not None and hasattr(kpts, "xy") and idx < len(kpts.xy):
                keypoints = kpts.xy[idx].tolist()

            detections.append(
                {
                    "bbox": [
                        int(box.xyxy[0][0]),
                        int(box.xyxy[0][1]),
                        int(box.xyxy[0][2]),
                        int(box.xyxy[0][3]),
                    ],
                    "confidence": float(box.conf[0]),
                    "label": "pose",
                    "keypoints": keypoints,
                }
            )

    return detections
