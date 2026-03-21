from flask import Flask, request, jsonify
import os
from datetime import datetime
import json

app = Flask(__name__)

UPLOAD_FOLDER = "incoming/quarantine"
LOG_FILE = "upload_log.jsonl"

ALLOWED_EXTENSIONS = {"mp4", "mov", "webm", "wav", "mp3"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def log_upload(data):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")

@app.route("/api/upload", methods=["POST"])
def upload():
    destination = request.form.get("destination", "")
    submitter_name = request.form.get("submitter_name", "")
    submitter_email = request.form.get("submitter_email", "")
    notes = request.form.get("notes", "")
    submitted_at = request.form.get("submitted_at", "")

    if "files" not in request.files:
        return jsonify({"status": "error", "message": "No files provided"}), 400

    files = request.files.getlist("files")
    saved_files = []

    for file in files:
        if file.filename == "":
            continue

        if not allowed_file(file.filename):
            return jsonify({"status": "error", "message": f"Invalid file type: {file.filename}"}), 400

        filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        file.save(filepath)
        saved_files.append(filename)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "destination": destination,
        "submitter_name": submitter_name,
        "submitter_email": submitter_email,
        "notes": notes,
        "submitted_at": submitted_at,
        "files": saved_files
    }

    log_upload(log_entry)

    return jsonify({
        "status": "ok",
        "message": "Files received and saved to quarantine.",
        "files": saved_files
    })
