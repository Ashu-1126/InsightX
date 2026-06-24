import os
import cv2
from datetime import datetime

INCIDENT_CLIPS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../Database/incident_clips")
)
INCIDENT_IMAGES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../Database/incident_images")
)
os.makedirs(INCIDENT_CLIPS_DIR, exist_ok=True)
os.makedirs(INCIDENT_IMAGES_DIR, exist_ok=True)


def save_incident_clip(frames, incident_type):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{incident_type}_{timestamp}.mp4"
    filepath = os.path.join(INCIDENT_CLIPS_DIR, filename)
    if not frames:
        return None
    height, width, _ = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(filepath, fourcc, 20.0, (width, height))
    for frame in frames:
        out.write(frame)
    out.release()
    return filepath


def save_incident_snapshot(frame, incident_type):
    if frame is None:
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{incident_type}_{timestamp}.jpg"
    filepath = os.path.join(INCIDENT_IMAGES_DIR, filename)
    ok = cv2.imwrite(filepath, frame)
    return filepath if ok else None
