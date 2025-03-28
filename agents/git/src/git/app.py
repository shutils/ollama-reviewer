import subprocess
from flask import Flask, jsonify

def create_app():
    app = Flask(__name__)
    
    @app.route("/", methods=["GET"])
    def root():
        return "hello"

    @app.route("/git-diff", methods=["GET"])
    def git_diff():
        try:
            result = subprocess.run(
                ["git", "-C", "/target", "diff"],
                capture_output=True,
                text=True,
                check=True
            )
            return jsonify({"diff": result.stdout})
        except subprocess.CalledProcessError as e:
            return jsonify({"error": e.stderr}), 500
    
    return app
