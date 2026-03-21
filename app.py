from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

UPLOAD_PASSWORD = os.environ.get("UPLOAD_PASSWORD", "")

@app.route("/api/upload", methods=["POST"])
def upload():
    submitter_name = request.form.get("submitter_name", "").strip()
    submitter_email = request.form.get("submitter_email", "").strip()
    password = request.form.get("password", "").strip()
    notes = request.form.get("notes", "").strip()

    if not submitter_name:
        return jsonify({"status": "error", "message": "Full name is required"}), 400

    if " " not in submitter_name:
        return jsonify({"status": "error", "message": "Enter first and last name"}), 400

    if not submitter_email:
        return jsonify({"status": "error", "message": "Email is required"}), 400

    if not password:
        return jsonify({"status": "error", "message": "Password required"}), 400

    if not UPLOAD_PASSWORD or password != UPLOAD_PASSWORD:
        return jsonify({"status": "error", "message": "Invalid password"}), 403

    if not notes:
        return jsonify({"status": "error", "message": "Description is required"}), 400

    if "files" not in request.files:
        return jsonify({"status": "error", "message": "No files provided"}), 400

    files = request.files.getlist("files")
    saved = []

    for file in files:
        if file.filename == "":
            continue

        filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        path = os.path.join(UPLOAD_FOLDER, filename)

        file.save(path)
        saved.append(filename)

    if not saved:
        return jsonify({"status": "error", "message": "No valid files uploaded"}), 400

    return jsonify({
        "status": "ok",
        "message": "files saved",
        "files": saved
    })
