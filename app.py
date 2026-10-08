"""CalmBand backend entry point.

Run:   flask --app app run --host 0.0.0.0 --port 5000 --debug
"""
import os

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app)  # allow the web / mobile front end to call this server

    # SQLite cannot create the folder itself
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if uri.startswith("sqlite:///") and ":memory:" not in uri:
        os.makedirs(os.path.dirname(uri[len("sqlite:///"):]) or ".", exist_ok=True)

    if app.config["SECRET_KEY"] == "dev-secret-change-me" and not app.config.get("TESTING"):
        app.logger.warning("SECRET_KEY is the default value. Set the SECRET_KEY environment variable before real use.")

    db.init_app(app)
    import models  # noqa: F401  (registers the tables)
    with app.app_context():
        db.create_all()

    from routes.auth_routes import bp as auth_bp
    from routes.dashboard_routes import bp as dashboard_bp
    from routes.device_routes import bp as device_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(device_bp)

    import cli
    cli.register(app)

    @app.get("/")
    def root():
        return jsonify({"message": "CalmBand API is running"})

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"status": "error", "message": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(_):
        return jsonify({"status": "error", "message": "Server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
