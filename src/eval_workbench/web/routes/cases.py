from flask import Blueprint, jsonify, request, current_app

from src.eval_workbench.services import cases as cases_service
from src.eval_workbench.services.errors import ServiceError

cases_bp = Blueprint("cases", __name__)


@cases_bp.route("/", methods=["GET"])
def list_cases():
    return jsonify(cases_service.list_cases(current_app.config["REPO_PATH"]))


@cases_bp.route("/", methods=["POST"])
def create_case():
    data = request.json
    return jsonify(
        cases_service.create_case(
            current_app.config["REPO_PATH"],
            data,
            dataset_id=data.get("dataset_id"),
        )
    )


@cases_bp.route("/generate", methods=["POST"])
def generate_case():
    data = request.json or {}
    try:
        return jsonify(
            cases_service.generate_case(
                current_app.config["REPO_PATH"],
                data.get("snapshot_id"),
                data.get("specification", ""),
            )
        )
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@cases_bp.route("/<case_id>", methods=["GET"])
def get_case(case_id):
    case = cases_service.get_case(current_app.config["REPO_PATH"], case_id)
    if case:
        return jsonify(case)
    return jsonify({"error": "not found"}), 404
