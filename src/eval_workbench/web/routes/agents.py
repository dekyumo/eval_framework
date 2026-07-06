from flask import Blueprint, jsonify, request, current_app

from src.eval_workbench.services import agents as agents_service
from src.eval_workbench.services.errors import ServiceError

agents_bp = Blueprint("agents", __name__)


@agents_bp.route("/snapshots", methods=["GET"])
def get_snapshots():
    try:
        return jsonify(agents_service.list_snapshots(current_app.config["REPO_PATH"]))
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@agents_bp.route("/snapshots/<id>", methods=["GET"])
def get_snapshot(id):
    snapshot = agents_service.get_snapshot(current_app.config["REPO_PATH"], id)
    if snapshot:
        return jsonify(snapshot)
    return jsonify({}), 404


@agents_bp.route("/scan", methods=["POST"])
def scan():
    data = request.json
    try:
        result = agents_service.scan(
            current_app.config["REPO_PATH"],
            data["agent_target"],
            data["commit"],
        )
        return jsonify(result)
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
