from flask import Blueprint, jsonify, request, current_app

from pydantic import ValidationError

from src.eval_workbench.domain.blueprint import AgentBlueprint
from src.eval_workbench.services import blueprints as blueprints_service
from src.eval_workbench.services.errors import ServiceError

blueprints_bp = Blueprint("blueprints", __name__)


@blueprints_bp.route("/presets", methods=["GET"])
def list_presets():
    try:
        presets = blueprints_service.list_presets()
        return jsonify([preset.model_dump() for preset in presets])
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@blueprints_bp.route("/run", methods=["POST"])
def run_blueprint():
    try:
        blueprint = AgentBlueprint.model_validate(request.json or {})
        result = blueprints_service.run_blueprint(current_app.config["REPO_PATH"], blueprint)
        return jsonify(result.model_dump())
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
