import os, uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from .models import db, Conversation

bp_uploads = Blueprint("uploads", __name__, url_prefix="/api/uploads")

ALLOWED_EXT = {"mp3","wav","m4a","mp4","webm","ogg","aac","flac"}

@bp_uploads.post("")
def upload_media():
    if "file" not in request.files:
        return jsonify(ok=False, code="bad_request", message="No file part"), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify(ok=False, code="bad_request", message="No selected file"), 400
    ext = f.filename.rsplit(".",1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return jsonify(ok=False, code="unsupported_type"), 415

    os.makedirs("uploads", exist_ok=True)
    fname = f"{uuid.uuid4().hex}-{secure_filename(f.filename)}"
    path = os.path.join("uploads", fname)
    f.save(path)

    # Create conversation shell linked to this upload (ready for background transcription later)
    conv = Conversation(title=f"Upload: {f.filename}", status="draft", source="upload")
    db.session.add(conv); db.session.commit()

    return jsonify(ok=True, id=conv.id, filename=f.filename, stored=fname)