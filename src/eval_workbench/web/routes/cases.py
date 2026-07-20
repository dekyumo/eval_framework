from flask import Blueprint, jsonify, request, current_app

from pydantic import ValidationError

from src.eval_workbench.agents.case_writer.case_writer_runner import draft_to_dict
from src.eval_workbench.domain.case import EvalCase
from src.eval_workbench.services import cases as cases_service
from src.eval_workbench.services.errors import ServiceError

cases_bp = Blueprint("cases", __name__)


@cases_bp.route("/", methods=["GET"])
def list_cases():
    active_only = request.args.get("active_only", "").lower() in {"1", "true", "yes"}
    cases = cases_service.list_cases(current_app.config["REPO_PATH"], active_only=active_only)
    return jsonify([case.model_dump() for case in cases])


@cases_bp.route("/", methods=["POST"])
def create_case():
    body = dict(request.json or {})
    from_version_of = body.pop("from_version_of", None)
    try:
        case = EvalCase.model_validate(body)
        created = cases_service.create_case(
            current_app.config["REPO_PATH"],
            case,
            from_version_of=from_version_of,
        )
        return jsonify(created.model_dump())
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@cases_bp.route("/generate", methods=["POST"])
def generate_case():
    data = request.json or {}
    try:
        draft = cases_service.generate_case(
            current_app.config["REPO_PATH"],
            data.get("snapshot_id"),
            data.get("specification", ""),
        )
        return jsonify(draft_to_dict(draft))
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@cases_bp.route("/<case_id>", methods=["GET"])
def get_case(case_id):
    case = cases_service.get_case(current_app.config["REPO_PATH"], case_id)
    if case:
        return jsonify(case.model_dump())
    return jsonify({"error": "not found"}), 404


@cases_bp.route("/<case_id>", methods=["PUT"])
def update_case(case_id):
    body = dict(request.json or {})
    cascade = request.args.get("cascade", "").lower() in {"1", "true", "yes"}
    existing = cases_service.get_case(current_app.config["REPO_PATH"], case_id)
    if not existing:
        return jsonify({"error": "not found"}), 404
    body["id"] = case_id
    try:
        merged = existing.model_dump()
        merged.update(body)
        case = EvalCase.model_validate(merged)
        updated = cases_service.update_case(
            current_app.config["REPO_PATH"],
            case,
            cascade=cascade,
        )
        return jsonify(updated.model_dump())
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@cases_bp.route("/<case_id>/impact", methods=["GET"])
def case_impact(case_id):
    try:
        impact = cases_service.get_case_impact(current_app.config["REPO_PATH"], case_id)
        return jsonify(impact.model_dump())
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@cases_bp.route("/<case_id>/deactivate", methods=["POST"])
def deactivate_case(case_id):
    try:
        case = cases_service.deactivate_case(current_app.config["REPO_PATH"], case_id)
        return jsonify(case.model_dump())
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
