from flask import Blueprint, jsonify, request, current_app

from src.eval_workbench.services import campaigns as campaigns_service
from src.eval_workbench.services.errors import ServiceError

campaigns_bp = Blueprint("campaigns", __name__)


@campaigns_bp.route("/", methods=["GET"])
def list_campaigns():
    return jsonify(campaigns_service.list_campaigns(current_app.config["REPO_PATH"]))


@campaigns_bp.route("/", methods=["POST"])
def create_campaign():
    return jsonify(campaigns_service.create_campaign(current_app.config["REPO_PATH"], request.json))


@campaigns_bp.route("/<camp_id>/matrix", methods=["GET"])
def get_matrix(camp_id):
    try:
        metric = request.args.get("metric")
        return jsonify(
            campaigns_service.get_matrix(
                current_app.config["REPO_PATH"],
                camp_id,
                metric_name=metric,
            )
        )
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
