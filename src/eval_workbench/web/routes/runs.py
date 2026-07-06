from flask import Blueprint, jsonify, request, current_app

from src.eval_workbench.services import runs as runs_service
from src.eval_workbench.services.errors import ServiceError

runs_bp = Blueprint("runs", __name__)


@runs_bp.route("/generate", methods=["POST"])
def generate_run():
    data = request.json
    try:
        return jsonify(
            runs_service.generate_run(
                current_app.config["REPO_PATH"],
                data.get("snapshot_id"),
                data.get("case_id"),
                data.get("model_id"),
                force=bool(data.get("force", False)),
            )
        )
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@runs_bp.route("/", methods=["GET"])
def list_runs():
    return jsonify(runs_service.list_runs(current_app.config["REPO_PATH"]))


@runs_bp.route("/scored", methods=["GET"])
def list_scored_runs():
    return jsonify(runs_service.list_scored_runs(current_app.config["REPO_PATH"]))


@runs_bp.route("/evaluate", methods=["POST"])
def evaluate_run():
    data = request.json
    try:
        return jsonify(
            runs_service.evaluate_run(
                current_app.config["REPO_PATH"],
                data.get("run_id"),
            )
        )
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
