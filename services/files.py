# services/files.py
import os
from typing import Tuple
from flask import current_app, send_file, abort

def session_dir(session_id: str) -> str:
    base = current_app.config["METRICS_DIR"]
    path = os.path.join(base, "sessions", session_id)
    os.makedirs(path, exist_ok=True)
    return path

def session_audio_path(session_id: str) -> str:
    return os.path.join(session_dir(session_id), "audio.webm")

def session_transcript_path(session_id: str) -> str:
    return os.path.join(session_dir(session_id), "transcript.txt")

def ensure_file_download(path: str, download_name: str) -> Tuple[str, str]:
    if not os.path.isfile(path) or os.path.getsize(path) <= 0:
        abort(404)
    return send_file(path, as_attachment=True, download_name=download_name), "ok"