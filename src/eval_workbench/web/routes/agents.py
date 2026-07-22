from flask import Blueprint, jsonify, request, current_app

from pydantic import ValidationError

from src.eval_workbench.domain.snapshot import AgentTarget
from src.eval_workbench.services import agents as agents_service
from src.eval_workbench.services import comparison as comparison_service
from src.eval_workbench.services.errors import ServiceError

agents_bp = Blueprint("agents", __name__)


@agents_bp.route("/snapshots", methods=["GET"])
def get_snapshots():
    try:
        snapshots = agents_service.list_snapshots(current_app.config["REPO_PATH"])
        return jsonify([snapshot.model_dump() for snapshot in snapshots])
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@agents_bp.route("/snapshots/<id>", methods=["GET"])
def get_snapshot(id):
    snapshot = agents_service.get_snapshot(current_app.config["REPO_PATH"], id)
    if snapshot:
        return jsonify(snapshot.model_dump())
    return jsonify({}), 404


@agents_bp.route("/compare", methods=["POST"])
def compare_snapshots():
    data = request.json or {}
    snapshot_a = data.get("snapshot_a")
    snapshot_b = data.get("snapshot_b")
    if not snapshot_a or not snapshot_b:
        return jsonify({"error": "snapshot_a and snapshot_b are required"}), 400
    try:
        result = comparison_service.compare_snapshots(
            current_app.config["REPO_PATH"],
            snapshot_a,
            snapshot_b,
        )
        return jsonify(result.model_dump())
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@agents_bp.route("/scan", methods=["POST"])
def scan():
    data = request.json or {}
    try:
        target = AgentTarget.model_validate(
            {**data["agent_target"], "repo_path": current_app.config["REPO_PATH"]}
        )
        snapshot = agents_service.scan(
            current_app.config["REPO_PATH"],
            target,
            data["commit"],
        )
        return jsonify(snapshot.model_dump())
    except (KeyError, ValidationError) as exc:
        return jsonify({"error": str(exc)}), 400
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
