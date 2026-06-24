import os
from ultralytics import YOLO
import torch

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "../Models/Fire_Smoke/Fire_Smoke/last.pt",
)
_fire_model = None


def get_fire_model():
    global _fire_model
    if _fire_model is None and os.path.exists(MODEL_PATH):
        _fire_model = YOLO(MODEL_PATH)
    return _fire_model


def unload_fire_model() -> None:
    global _fire_model
    _fire_model = None


def detect_fire_smoke(img, conf_threshold=0.15, device=None):
    model = get_fire_model()
    if not model:
        return []
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    results = model(img, conf=conf_threshold, device=device)
    detections = []
    model_names = getattr(model, "names", {})
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            raw_label = model_names.get(cls, str(cls))
            label = str(raw_label).strip().lower()
            if conf >= conf_threshold:
                detections.append(
                    {
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "confidence": conf,
                        "label": label,
                    }
                )
    return detections
