from flask import Blueprint, jsonify, request, current_app

from pydantic import ValidationError

from src.eval_workbench.domain.campaign import EvalCampaign
from src.eval_workbench.services import campaigns as campaigns_service
from src.eval_workbench.services.errors import ServiceError

campaigns_bp = Blueprint("campaigns", __name__)


@campaigns_bp.route("/", methods=["GET"])
def list_campaigns():
    campaigns = campaigns_service.list_campaigns(current_app.config["REPO_PATH"])
    return jsonify([campaign.model_dump() for campaign in campaigns])


@campaigns_bp.route("/", methods=["POST"])
def create_campaign():
    try:
        campaign = EvalCampaign.model_validate(request.json or {})
        created = campaigns_service.create_campaign(current_app.config["REPO_PATH"], campaign)
        return jsonify(created.model_dump())
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400


@campaigns_bp.route("/<camp_id>/matrix", methods=["GET"])
def get_matrix(camp_id):
    try:
        metric = request.args.get("metric")
        matrix = campaigns_service.get_matrix(
            current_app.config["REPO_PATH"],
            camp_id,
            metric_name=metric,
        )
        return jsonify(matrix.model_dump())
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
