from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/upload", methods=["POST"])
def upload():
    return jsonify({"status": "ok", "message": "test response"})
