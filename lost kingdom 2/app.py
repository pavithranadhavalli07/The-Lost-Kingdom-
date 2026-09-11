import os
from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from config import Config
from models import db
from agents.orchestrator import MultiAgentOrchestrator
from routes.api import api_bp
from routes.sockets import register_socket_handlers

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # Initialize extensions
    CORS(app, resources={r"/*": {"origins": "*"}})
    db.init_app(app)
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

    # Create tables
    with app.app_context():
        db.create_all()

    # Initialize Multi-Agent Orchestrator
    orchestrator = MultiAgentOrchestrator(socketio=socketio)
    app.orchestrator = orchestrator

    # Register blueprints & socket handlers
    app.register_blueprint(api_bp)
    register_socket_handlers(socketio, orchestrator)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, "static"),
            "favicon.ico",
            mimetype="image/vnd.microsoft.icon"
        )

    return app, socketio

app, socketio = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"================================================================")
    print(f"  * Lost Kingdom 2: Autonomous Multi-Agent Educational Game")
    print(f"  * Orchestrator loaded 5 Autonomous AI Agents")
    print(f"  * Running on http://127.0.0.1:{port}")
    print(f"================================================================")
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)
