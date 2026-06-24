import os
from ultralytics import YOLO


# Adjust the model path as needed
def find_model():
    models_dir = os.path.join(os.path.dirname(__file__), "../Models")
    for root, dirs, files in os.walk(models_dir):
        for file in files:
            if "restricted" in file.lower() and file.endswith(".pt"):
                return os.path.join(root, file)
    return None


MODEL_PATH = find_model()
restricted_model = (
    YOLO(MODEL_PATH) if MODEL_PATH and os.path.exists(MODEL_PATH) else None
)


def detect_restricted_area(img):
    if not restricted_model:
        return []
    results = restricted_model(img)
    detections = []
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            conf = float(box.conf[0])
            detections.append(
                {
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": conf,
                    "label": "Restricted",
                }
            )
    return detections
