from flask import Blueprint, jsonify, request, current_app

from src.eval_workbench.services import governance as governance_service
from src.eval_workbench.services.errors import ServiceError

governance_bp = Blueprint("governance", __name__)


@governance_bp.route("/<snapshot_id>", methods=["GET"])
def get_governance(snapshot_id):
    try:
        return jsonify(governance_service.get_governance(current_app.config["REPO_PATH"], snapshot_id))
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@governance_bp.route("/<snapshot_id>", methods=["POST"])
def update_governance(snapshot_id):
    try:
        return jsonify(
            governance_service.update_governance(
                current_app.config["REPO_PATH"], snapshot_id, request.json or {}
            )
        )
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
