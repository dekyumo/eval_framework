from flask import Blueprint, jsonify, request, current_app

from src.eval_workbench.services import cases as cases_service
from src.eval_workbench.services.errors import ServiceError

cases_bp = Blueprint("cases", __name__)


@cases_bp.route("/", methods=["GET"])
def list_cases():
    active_only = request.args.get("active_only", "").lower() in {"1", "true", "yes"}
    return jsonify(cases_service.list_cases(current_app.config["REPO_PATH"], active_only=active_only))


@cases_bp.route("/", methods=["POST"])
def create_case():
    data = request.json or {}
    try:
        return jsonify(
            cases_service.create_case(
                current_app.config["REPO_PATH"],
                data,
                dataset_id=data.get("dataset_id"),
            )
        )
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


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


@cases_bp.route("/<case_id>", methods=["PUT"])
def update_case(case_id):
    data = request.json or {}
    cascade = request.args.get("cascade", "").lower() in {"1", "true", "yes"}
    try:
        return jsonify(
            cases_service.update_case(
                current_app.config["REPO_PATH"],
                case_id,
                data,
                cascade=cascade,
            )
        )
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@cases_bp.route("/<case_id>/impact", methods=["GET"])
def case_impact(case_id):
    try:
        return jsonify(cases_service.get_case_impact(current_app.config["REPO_PATH"], case_id))
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@cases_bp.route("/<case_id>/deactivate", methods=["POST"])
def deactivate_case(case_id):
    try:
        return jsonify(cases_service.deactivate_case(current_app.config["REPO_PATH"], case_id))
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
