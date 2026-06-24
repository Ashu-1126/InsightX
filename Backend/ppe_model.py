import os
from ultralytics import YOLO

CLASS_NAMES = [
    "Hardhat",
    "Mask",
    "NO-Hardhat",
    "NO-Mask",
    "NO-Safety Vest",
    "Person",
    "Safety Cone",
    "Safety Vest",
    "machinery",
    "vehicle",
]
MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "../Models/PPE-Detection/ppe.pt"
)
_ppe_model = None


def get_ppe_model():
    global _ppe_model
    if _ppe_model is None and os.path.exists(MODEL_PATH):
        _ppe_model = YOLO(MODEL_PATH)
    return _ppe_model


def unload_ppe_model() -> None:
    global _ppe_model
    _ppe_model = None


def detect_ppe(img):
    model = get_ppe_model()
    if not model:
        return []
    results = model(img)
    detections = []
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            label = CLASS_NAMES[cls] if cls < len(CLASS_NAMES) else str(cls)
            detections.append(
                {
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": conf,
                    "label": label,
                }
            )
    return detections
