from flask import Blueprint, jsonify, request, current_app

from src.eval_workbench.services import runs as runs_service
from src.eval_workbench.services.errors import ServiceError

runs_bp = Blueprint("runs", __name__)


@runs_bp.route("/generate", methods=["POST"])
def generate_run():
    data = request.json or {}
    try:
        run = runs_service.generate_run(
            current_app.config["REPO_PATH"],
            data.get("snapshot_id"),
            data.get("case_id"),
            data.get("model_id"),
            force=bool(data.get("force", False)),
        )
        return jsonify(run.model_dump())
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@runs_bp.route("/", methods=["GET"])
def list_runs():
    runs = runs_service.list_runs(current_app.config["REPO_PATH"])
    return jsonify([run.model_dump() for run in runs])


@runs_bp.route("/scored", methods=["GET"])
def list_scored_runs():
    runs = runs_service.list_scored_runs(current_app.config["REPO_PATH"])
    return jsonify([run.model_dump() for run in runs])


@runs_bp.route("/evaluate", methods=["POST"])
def evaluate_run():
    data = request.json or {}
    try:
        scored = runs_service.evaluate_run(
            current_app.config["REPO_PATH"],
            data.get("run_id"),
            force=bool(data.get("force", False)),
        )
        return jsonify(scored.model_dump())
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
