from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/api/upload", methods=["POST"])
def upload():
    submitter_name = request.form.get("submitter_name", "").strip()
    submitter_email = request.form.get("submitter_email", "").strip()
    password = request.form.get("password", "").strip()

    if not submitter_name:
        return jsonify({"status": "error", "message": "Submitter name is required"}), 400

    if not submitter_email:
        return jsonify({"status": "error", "message": "Email is required"}), 400

    if not password:
        return jsonify({"status": "error", "message": "Password is required"}), 400

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

    return jsonify({
        "status": "ok",
        "message": "files saved",
        "files": saved
    })
