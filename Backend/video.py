from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import cv2
from camera_stream import (
    ensure_camera_started,
    get_camera_index,
    get_frame,
    set_camera_index,
)
from live_session import deactivate_models
from model_runtime import sleep_all_models
from live_detection_utils import gen_live_detection

router = APIRouter()


def gen_raw_video():
    if not ensure_camera_started():
        raise HTTPException(status_code=503, detail="Camera is not available")
    while True:
        frame = get_frame(timeout_seconds=1.0)
        if frame is None:
            continue
        encoded, buffer = cv2.imencode(".jpg", frame)
        if not encoded:
            continue
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )


@router.get("/video_feed")
def video_feed():
    # Raw stream selection should stop any active model stream.
    deactivate_models()
    sleep_all_models()
    return StreamingResponse(
        gen_raw_video(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.post("/monitoring/stop")
def stop_monitoring():
    deactivate_models()
    sleep_all_models()
    return {"message": "Monitoring stopped. Models are sleeping."}


@router.post("/monitoring/camera/{camera_id}")
def set_monitoring_camera(camera_id: int):
    if camera_id < 0:
        raise HTTPException(status_code=400, detail="Invalid camera id")

    ok = set_camera_index(camera_id)
    if not ok:
        raise HTTPException(
            status_code=503,
            detail=f"Camera {camera_id} is not available",
        )

    return {
        "message": "Monitoring camera updated",
        "camera_id": get_camera_index(),
    }


@router.get("/monitoring/camera")
def get_monitoring_camera():
    return {"camera_id": get_camera_index()}


@router.get("/live/ppe")
def live_ppe():
    return StreamingResponse(
        gen_live_detection("ppe"),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/live/fire-smoke")
def live_fire_smoke():
    return StreamingResponse(
        gen_live_detection("fire-smoke"),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/live/fall")
def live_fall():
    return StreamingResponse(
        gen_live_detection("fall"),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/live/pose")
def live_pose():
    return StreamingResponse(
        gen_live_detection("pose"),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
