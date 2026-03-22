from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "/var/data/mirror_intake/quarantine"
MANIFEST_FILE = "/var/data/mirror_intake/upload_manifest.jsonl"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

UPLOAD_PASSWORD = os.environ.get("UPLOAD_PASSWORD", "")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY", "").strip()
MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN", "").strip()
NOTIFY_EMAIL_TO = os.environ.get("NOTIFY_EMAIL_TO", "rick@ignitelongevity.com").strip()
NOTIFY_EMAIL_FROM = os.environ.get("NOTIFY_EMAIL_FROM", "").strip()

def append_manifest_record(record):
    with open(MANIFEST_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

def is_admin(req):
    header_token = req.headers.get("x-admin-token", "")
    query_token = req.args.get("admin_token", "")
    token = header_token or query_token
    return bool(token) and token == ADMIN_TOKEN

@app.route("/api/intake/list", methods=["GET"])
def list_intake():
    if not is_admin(request):
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    files = sorted(os.listdir(UPLOAD_FOLDER))
    return jsonify({
        "status": "ok",
        "files": files
    })

@app.route("/api/intake/download/<path:filename>", methods=["GET"])
def download_file(filename):
    if not is_admin(request):
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

def send_notification_email(submitter_name, submitter_email, destination, notes, saved_files, submission_id):
    if not MAILGUN_API_KEY or not MAILGUN_DOMAIN or not NOTIFY_EMAIL_FROM:
        return {
            "sent": False,
            "reason": "mailgun_not_configured"
        }

    subject = f"Mirror upload received: {destination}"
    body = (
        f"Mirror upload received.\n\n"
        f"Submission ID: {submission_id}\n"
        f"Name: {submitter_name}\n"
        f"Email: {submitter_email}\n"
        f"Destination: {destination}\n"
        f"Description: {notes}\n"
        f"Files: {', '.join(saved_files)}\n"
        f"Timestamp UTC: {datetime.utcnow().isoformat()}\n"
    )

    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data={
                "from": NOTIFY_EMAIL_FROM,
                "to": [NOTIFY_EMAIL_TO],
                "subject": subject,
                "text": body,
            },
            timeout=20,
        )

        return {
            "sent": response.ok,
            "status_code": response.status_code
        }
    except Exception as e:
        return {
            "sent": False,
            "reason": str(e)
        }

@app.route("/api/upload", methods=["POST"])
def upload():
    submitter_name = request.form.get("submitter_name", "").strip()
    submitter_email = request.form.get("submitter_email", "").strip()
    password = request.form.get("password", "").strip()
    notes = request.form.get("notes", "").strip()
    destination = request.form.get("destination", "").strip()

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

    # create submission id once per upload
    submission_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    for idx, file in enumerate(files, start=1):
        if file.filename == "":
            continue

        filename = f"{submission_id}_{idx:02d}_{file.filename}"
        path = os.path.join(UPLOAD_FOLDER, filename)

        file.save(path)
        saved.append(filename)

    if not saved:
        return jsonify({"status": "error", "message": "No valid files uploaded"}), 400

    manifest_record = {
        "submission_id": submission_id,
        "timestamp_utc": datetime.utcnow().isoformat(),
        "submitter_name": submitter_name,
        "submitter_email": submitter_email,
        "destination": destination,
        "notes": notes,
        "saved_files": saved
    }
    append_manifest_record(manifest_record)

    email_result = send_notification_email(
        submitter_name=submitter_name,
        submitter_email=submitter_email,
        destination=destination,
        notes=notes,
        saved_files=saved,
        submission_id=submission_id
    )

    return jsonify({
        "status": "ok",
        "message": "Submission received successfully. Your file was accepted and placed in intake.",
        "submission_id": submission_id,
        "files": saved,
        "notification": email_result,
    })
