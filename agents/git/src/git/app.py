from flask import Flask

def create_app():
    app = Flask(__name__)
    
    @app.route("/", methods=["GET"])
    def root():
        return "hello"
    
    return app
