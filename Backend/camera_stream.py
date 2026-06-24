import sys
import threading
import time

import cv2


class SharedCamera:
    def __init__(self, index: int = 0):
        self.index = index
        self.cap = None
        self._frame = None
        self._running = False
        self._lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._thread = None

    def start(self) -> bool:
        with self._state_lock:
            return self._start_unlocked()

    def _start_unlocked(self) -> bool:
        if self._running and self.cap is not None and self.cap.isOpened():
            return True

        backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else None
        self.cap = (
            cv2.VideoCapture(self.index, backend)
            if backend is not None
            else cv2.VideoCapture(self.index)
        )

        if not self.cap.isOpened():
            self.cap = None
            return False

        self._running = True
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()
        return True

    def _reader(self) -> None:
        while self._running and self.cap is not None:
            ok, frame = self.cap.read()
            if ok:
                with self._lock:
                    self._frame = frame
            else:
                time.sleep(0.02)

    def get_latest_frame(self):
        with self._lock:
            if self._frame is None:
                return None
            return self._frame.copy()

    def stop(self) -> None:
        with self._state_lock:
            self._stop_unlocked()

    def _stop_unlocked(self) -> None:
        self._running = False
        thread = self._thread
        self._thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=0.3)
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def set_camera_index(self, index: int) -> bool:
        with self._state_lock:
            if (
                index == self.index
                and self.cap is not None
                and self.cap.isOpened()
            ):
                return True
            self._stop_unlocked()
            self.index = index
            return self._start_unlocked()

    def get_camera_index(self) -> int:
        with self._state_lock:
            return self.index


_shared_camera = SharedCamera(index=0)


def ensure_camera_started() -> bool:
    return _shared_camera.start()


def set_camera_index(index: int) -> bool:
    return _shared_camera.set_camera_index(index)


def get_camera_index() -> int:
    return _shared_camera.get_camera_index()


def get_frame(timeout_seconds: float = 1.0):
    start = time.time()
    while time.time() - start < timeout_seconds:
        frame = _shared_camera.get_latest_frame()
        if frame is not None:
            return frame
        time.sleep(0.01)
    return None
