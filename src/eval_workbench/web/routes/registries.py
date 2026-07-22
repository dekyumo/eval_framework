from flask import Blueprint, jsonify, request, current_app

from pydantic import ValidationError

from src.eval_workbench.domain.case import EvalDataset
from src.eval_workbench.domain.extractor import Extractor
from src.eval_workbench.domain.gym import Gym
from src.eval_workbench.domain.rubric import Rubric
from src.eval_workbench.domain.tag import Tag
from src.eval_workbench.services import registries as registries_service
from src.eval_workbench.services.errors import ServiceError

registries_bp = Blueprint("registries", __name__)


def _rubric_api_dump(rubric: Rubric) -> dict:
    data = rubric.model_dump()
    for item in data.get("items", []):
        item["description"] = item.get("prompt", "")
    return data


def _rubric_from_api(body: dict) -> Rubric:
    payload = dict(body)
    for item in payload.get("items", []):
        if item.get("description") and not item.get("prompt"):
            item["prompt"] = item["description"]
    return Rubric.model_validate(payload)


@registries_bp.route("/tags", methods=["GET"])
def list_tags():
    tags = registries_service.list_tags(current_app.config["REPO_PATH"])
    return jsonify([tag.model_dump() for tag in tags])


@registries_bp.route("/datasets", methods=["GET"])
def list_datasets():
    datasets = registries_service.list_datasets(current_app.config["REPO_PATH"])
    return jsonify([dataset.model_dump() for dataset in datasets])


@registries_bp.route("/rubrics", methods=["GET"])
def list_rubrics():
    rubrics = registries_service.list_rubrics(current_app.config["REPO_PATH"])
    return jsonify([_rubric_api_dump(rubric) for rubric in rubrics])


@registries_bp.route("/extractors", methods=["GET"])
def list_extractors():
    extractors = registries_service.list_extractors(current_app.config["REPO_PATH"])
    return jsonify([extractor.model_dump() for extractor in extractors])


@registries_bp.route("/gyms", methods=["GET"])
def list_gyms():
    gyms = registries_service.list_gyms(current_app.config["REPO_PATH"])
    return jsonify([gym.model_dump() for gym in gyms])


@registries_bp.route("/tags", methods=["POST"])
def create_tag():
    data = dict(request.json or {})
    if not data.get("id"):
        data["id"] = data.get("name", "").strip().lower().replace(" ", "-")
    try:
        tag = Tag.model_validate(data)
        created = registries_service.create_tag(current_app.config["REPO_PATH"], tag)
        return jsonify(created.model_dump())
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400


@registries_bp.route("/datasets", methods=["POST"])
def create_dataset():
    try:
        dataset = EvalDataset.model_validate(request.json or {})
        created = registries_service.create_dataset(current_app.config["REPO_PATH"], dataset)
        return jsonify(created.model_dump())
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400


@registries_bp.route("/rubrics", methods=["POST"])
def create_rubric():
    try:
        rubric = _rubric_from_api(request.json or {})
        created = registries_service.create_rubric(current_app.config["REPO_PATH"], rubric)
        return jsonify(_rubric_api_dump(created))
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400


@registries_bp.route("/extractors", methods=["POST"])
def create_extractor():
    data = dict(request.json or {})
    python_code = data.pop("python_code", None) or "def extract(trace):\n    return True"
    try:
        extractor = Extractor.model_construct(
            id=data["id"],
            name=data["name"],
            return_type=data["return_type"],
            source_path="",
            fingerprint="",
        )
        created = registries_service.create_extractor(
            current_app.config["REPO_PATH"],
            extractor,
            python_code=python_code,
        )
        response = created.model_dump()
        response["python_code"] = python_code
        return jsonify(response)
    except (KeyError, ValidationError) as exc:
        return jsonify({"error": str(exc)}), 400
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@registries_bp.route("/gyms", methods=["POST"])
def create_gym():
    data = dict(request.json or {})
    if not data.get("id"):
        slug = data.get("name", "").strip().lower().replace(" ", "-")
        data["id"] = "".join(ch for ch in slug if ch.isalnum() or ch in "-_")
    try:
        gym = Gym.model_validate(data)
        created = registries_service.create_gym(current_app.config["REPO_PATH"], gym)
        return jsonify(created.model_dump())
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@registries_bp.route("/tags/<id>", methods=["DELETE"])
def delete_tag(id):
    try:
        registries_service.delete_tag(current_app.config["REPO_PATH"], id)
        return jsonify({"status": "deleted"})
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@registries_bp.route("/datasets/<id>", methods=["DELETE"])
def delete_dataset(id):
    try:
        registries_service.delete_dataset(current_app.config["REPO_PATH"], id)
        return jsonify({"status": "deleted"})
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@registries_bp.route("/rubrics/<id>", methods=["DELETE"])
def delete_rubric(id):
    try:
        registries_service.delete_rubric(current_app.config["REPO_PATH"], id)
        return jsonify({"status": "deleted"})
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@registries_bp.route("/extractors/<id>", methods=["DELETE"])
def delete_extractor(id):
    try:
        registries_service.delete_extractor(current_app.config["REPO_PATH"], id)
        return jsonify({"status": "deleted"})
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@registries_bp.route("/gyms/<id>", methods=["DELETE"])
def delete_gym(id):
    try:
        registries_service.delete_gym(current_app.config["REPO_PATH"], id)
        return jsonify({"status": "deleted"})
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@registries_bp.route("/extractors/generate", methods=["POST"])
def generate_extractor_code():
    data = request.json or {}
    try:
        code = registries_service.generate_extractor_code(data.get("description", ""))
        return jsonify({"code": code})
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
