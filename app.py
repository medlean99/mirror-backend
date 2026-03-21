from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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

    return jsonify({"status": "ok", "message": "validation passed"})
