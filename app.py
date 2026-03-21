from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "incoming/quarantine"
LOG_FILE = "upload_log.jsonl"
UPLOAD_PASSWORD = os.environ.get("UPLOAD_PASSWORD", "")

ALLOWED_EXTENSIONS = {"mp4", "mov", "webm", "wav", "mp3"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def log_upload(data):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")

@app.route("/api/upload", methods=["POST"])
def upload():
    destination = request.form.get("destination", "").strip()
    submitter_name = request.form.get("submitter_name", "").strip()
    submitter_email = request.form.get("submitter_email", "").strip()
    password = request.form.get("password", "").strip()
    notes = request.form.get("notes", "").strip()
    submitted_at = request.form.get("submitted_at", "").strip()

    if not submitter_name:
        return jsonify({"status": "error", "message": "Submitter name is required"}), 400

    if not submitter_email:
        return jsonify({"status": "error", "message": "Email is required"}), 400

    if not password:
        return jsonify({"status": "error", "message": "Password is required"}), 400

    if not UPLOAD_PASSWORD or password != UPLOAD_PASSWORD:
        return jsonify({"status": "error", "message": "Invalid password"}), 403

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

    if not saved_files:
        return jsonify({"status": "error", "message": "No valid files uploaded"}), 400

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
