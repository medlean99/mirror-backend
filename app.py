from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/api/upload", methods=["POST"])
def upload():
    print("REQUEST HIT")
    return "OK", 200
