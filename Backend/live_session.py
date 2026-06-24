import threading


_lock = threading.Lock()
_active_model: str | None = None
_session_id = 0


def activate_model(model_type: str) -> int:
    global _active_model, _session_id
    with _lock:
        _active_model = model_type
        _session_id += 1
        return _session_id


def deactivate_models() -> None:
    global _active_model, _session_id
    with _lock:
        _active_model = None
        _session_id += 1


def is_active(model_type: str, session_id: int) -> bool:
    with _lock:
        return _active_model == model_type and _session_id == session_id


def get_active_model() -> str | None:
    with _lock:
        return _active_model
