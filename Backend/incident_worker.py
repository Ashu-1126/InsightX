import asyncio
import json
import os
import threading
import time
import uuid

import numpy as np

from incident_service import create_incident
from incidents_storage import save_incident_clip, save_incident_snapshot
from realtime import broadcast_incident


JOBS_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../Database/incident_jobs")
)
PENDING_DIR = os.path.join(JOBS_ROOT, "pending")
FAILED_DIR = os.path.join(JOBS_ROOT, "failed")
MAX_RETRIES = 3

os.makedirs(PENDING_DIR, exist_ok=True)
os.makedirs(FAILED_DIR, exist_ok=True)

_worker_started = False
_worker_lock = threading.Lock()


def _job_paths(job_id: str) -> tuple[str, str]:
    meta_path = os.path.join(PENDING_DIR, f"{job_id}.json")
    frames_path = os.path.join(PENDING_DIR, f"{job_id}.npz")
    return meta_path, frames_path


def _write_job(job_id: str, job: dict, frames: list) -> None:
    meta_path, frames_path = _job_paths(job_id)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(job, f)

    frame_array = np.stack(frames) if frames else np.empty((0,))
    np.savez_compressed(frames_path, frames=frame_array)


def _load_job(job_id: str) -> tuple[dict, list]:
    meta_path, frames_path = _job_paths(job_id)
    with open(meta_path, "r", encoding="utf-8") as f:
        job = json.load(f)

    with np.load(frames_path, allow_pickle=False) as data:
        frames = data["frames"]
        frame_list = [frame.copy() for frame in frames] if len(frames) else []

    return job, frame_list


def _mark_failed(job_id: str, job: dict, reason: str) -> None:
    src_meta, src_frames = _job_paths(job_id)
    failed_meta = os.path.join(FAILED_DIR, f"{job_id}.json")
    failed_frames = os.path.join(FAILED_DIR, f"{job_id}.npz")
    job["failed_reason"] = reason
    with open(failed_meta, "w", encoding="utf-8") as f:
        json.dump(job, f)
    if os.path.exists(src_frames):
        os.replace(src_frames, failed_frames)
    if os.path.exists(src_meta):
        os.remove(src_meta)


def _remove_job(job_id: str) -> None:
    meta_path, frames_path = _job_paths(job_id)
    if os.path.exists(meta_path):
        os.remove(meta_path)
    if os.path.exists(frames_path):
        os.remove(frames_path)


def _list_pending_job_ids() -> list[str]:
    ids = []
    for name in os.listdir(PENDING_DIR):
        if name.endswith(".json"):
            ids.append(name[:-5])
    ids.sort()
    return ids


def _process_incident_job(job: dict, frames: list) -> None:
    model_type = job["model_type"]
    camera_id = job.get("camera_id")
    confidence = job.get("confidence")
    persistence_threshold = job.get("persistence_threshold", 5)

    clip_path = save_incident_clip(frames, model_type)
    snapshot_path = save_incident_snapshot(
        frames[0] if frames else None,
        model_type,
    )

    description = (
        f"{model_type} anomaly detected and persisted for "
        f"{persistence_threshold}s."
    )

    incident = create_incident(
        incident_type=model_type,
        description=description,
        clip_path=os.path.basename(clip_path) if clip_path else None,
        source="auto-monitoring",
        confidence=confidence,
        evidence_image=(
            os.path.basename(snapshot_path) if snapshot_path else None
        ),
        camera_id=camera_id,
    )

    try:
        asyncio.run(broadcast_incident(incident))
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to broadcast incident update: {exc}")


def _worker_loop() -> None:
    while True:
        processed = False
        for job_id in _list_pending_job_ids():
            processed = True
            try:
                job, frames = _load_job(job_id)
                _process_incident_job(job, frames)
                _remove_job(job_id)
            except Exception as exc:  # noqa: BLE001
                try:
                    job, _ = _load_job(job_id)
                except Exception:  # noqa: BLE001
                    _remove_job(job_id)
                    continue
                retries = int(job.get("retries", 0)) + 1
                job["retries"] = retries
                if retries >= MAX_RETRIES:
                    _mark_failed(job_id, job, str(exc))
                else:
                    meta_path, _ = _job_paths(job_id)
                    with open(meta_path, "w", encoding="utf-8") as f:
                        json.dump(job, f)
                    print(f"Incident job retry {retries}/{MAX_RETRIES}: {exc}")

        if not processed:
            time.sleep(0.5)


def start_incident_worker() -> None:
    global _worker_started
    with _worker_lock:
        if _worker_started:
            return
        worker = threading.Thread(target=_worker_loop, daemon=True)
        worker.start()
        _worker_started = True


def enqueue_incident_job(
    model_type: str,
    frames: list,
    confidence: float | None,
    persistence_threshold: int,
    camera_id: int | None,
) -> bool:
    if not frames:
        return False

    start_incident_worker()
    job_id = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    job = {
        "id": job_id,
        "model_type": model_type,
        "confidence": confidence,
        "persistence_threshold": persistence_threshold,
        "camera_id": camera_id,
        "retries": 0,
    }
    try:
        _write_job(job_id, job, frames)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to persist incident job: {exc}")
        return False
