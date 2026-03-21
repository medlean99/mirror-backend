from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

UPLOAD_PASSWORD = os.environ.get("UPLOAD_PASSWORD", "")

@app.route("/api/upload", methods=["POST"])
def upload():
    password = request.form.get("password", "").strip()

    return jsonify({
        "entered_password": password,
        "env_password": UPLOAD_PASSWORD,
        "match": password == UPLOAD_PASSWORD
    })
