import os
from flask import Flask, jsonify, request, send_from_directory

from src.eval_workbench.services import human_eval as human_eval_service
from src.eval_workbench.services import repo as repo_service


def create_app(repo_path=None):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    static_root = os.path.abspath(os.path.join(current_dir, "static"))
    static_assets = os.path.join(static_root, "assets")

    # Built-in static route only serves /assets/* so SPA paths like /agents reach serve().
    app = Flask(__name__, static_folder=static_assets, static_url_path="/assets")
    app.config["REPO_PATH"] = repo_path or os.getcwd()

    from src.eval_workbench.web.routes.agents import agents_bp
    from src.eval_workbench.web.routes.cases import cases_bp
    from src.eval_workbench.web.routes.runs import runs_bp
    from src.eval_workbench.web.routes.campaigns import campaigns_bp
    from src.eval_workbench.web.routes.registries import registries_bp

    app.register_blueprint(agents_bp, url_prefix="/api/agents")
    app.register_blueprint(cases_bp, url_prefix="/api/cases")
    app.register_blueprint(runs_bp, url_prefix="/api/runs")
    app.register_blueprint(campaigns_bp, url_prefix="/api/campaigns")
    app.register_blueprint(registries_bp, url_prefix="/api/registries")

    @app.route("/api/health")
    def health_check():
        return jsonify({"status": "ok"})

    @app.route("/api/test/reset", methods=["POST"])
    def test_reset():
        return jsonify(repo_service.reset_database(app.config["REPO_PATH"]))

    @app.route("/api/human-eval", methods=["POST"])
    def create_human_eval():
        return jsonify(human_eval_service.create_human_eval(app.config["REPO_PATH"], request.json))

    @app.route("/api/repo")
    def get_repo():
        return jsonify(repo_service.get_repo_path(app.config["REPO_PATH"]))

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve(path):
        if path.startswith("api/"):
            return jsonify({"error": "Not Found"}), 404
        if path != "" and os.path.exists(os.path.join(static_root, path)):
            return send_from_directory(static_root, path)
        return send_from_directory(static_root, "index.html")

    return app
