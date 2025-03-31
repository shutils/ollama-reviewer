import subprocess
from flask import Flask, jsonify, request
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    
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
    
    @app.route("/git-show", methods=["GET"])
    def git_show():
        commit_hash = request.args.get("commit_hash", "HEAD")
        file_path = request.args.get("file_path")
        
        if not file_path:
            return jsonify({"error": "Missing file_path"}), 400
        
        try:
            result = subprocess.run(
                ["git", "-C", "/target", "show", f"{commit_hash}:{file_path}"],
                capture_output=True,
                text=True,
                check=True
            )
            return jsonify({"file_content": result.stdout})
        except subprocess.CalledProcessError as e:
            return jsonify({"error": e.stderr}), 500
    
    @app.route("/git-file-ls", methods=["GET"])
    def git_file_ls():
        commit_hash = request.args.get("commit_hash", "HEAD")
        
        try:
            result = subprocess.run(
                ["git", "-C", "/target", "ls-tree", "--name-only", "-r", commit_hash],
                capture_output=True,
                text=True,
                check=True
            )
            return jsonify({"files": result.stdout.splitlines()})
        except subprocess.CalledProcessError as e:
            return jsonify({"error": e.stderr}), 500
    
    return app