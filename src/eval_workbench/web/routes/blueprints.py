from flask import Blueprint, jsonify, request, current_app

from src.eval_workbench.services import blueprints as blueprints_service
from src.eval_workbench.services.errors import ServiceError

blueprints_bp = Blueprint("blueprints", __name__)


@blueprints_bp.route("/presets", methods=["GET"])
def list_presets():
    try:
        return jsonify(blueprints_service.list_presets())
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@blueprints_bp.route("/run", methods=["POST"])
def run_blueprint():
    data = request.json or {}
    try:
        return jsonify(blueprints_service.run_blueprint(current_app.config["REPO_PATH"], data))
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
