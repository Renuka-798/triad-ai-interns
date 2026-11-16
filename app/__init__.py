
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from app.config import Config


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    # Enable JWT authentication
    JWTManager(app)

    # Enable frontend communication
    CORS(app)

    # Register authentication routes
    from app.routes import auth_bp
    app.register_blueprint(auth_bp)

    # Health check API
    @app.route("/api/health", methods=["GET"])
    def health():
        try:
            from app.models import client

            client.admin.command("ping")

            return jsonify({
                "status": "success",
                "message": "Flask and MongoDB connected successfully!"
            }), 200

        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    return app
