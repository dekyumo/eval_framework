from flask import Blueprint, jsonify, request, current_app

from src.eval_workbench.services import registries as registries_service
from src.eval_workbench.services.errors import ServiceError

registries_bp = Blueprint("registries", __name__)


@registries_bp.route("/tags", methods=["GET"])
def list_tags():
    return jsonify(registries_service.list_tags(current_app.config["REPO_PATH"]))


@registries_bp.route("/datasets", methods=["GET"])
def list_datasets():
    return jsonify(registries_service.list_datasets(current_app.config["REPO_PATH"]))


@registries_bp.route("/rubrics", methods=["GET"])
def list_rubrics():
    return jsonify(registries_service.list_rubrics(current_app.config["REPO_PATH"]))


@registries_bp.route("/extractors", methods=["GET"])
def list_extractors():
    return jsonify(registries_service.list_extractors(current_app.config["REPO_PATH"]))


@registries_bp.route("/gyms", methods=["GET"])
def list_gyms():
    return jsonify(registries_service.list_gyms(current_app.config["REPO_PATH"]))


@registries_bp.route("/tags", methods=["POST"])
def create_tag():
    return jsonify(registries_service.create_tag(current_app.config["REPO_PATH"], request.json))


@registries_bp.route("/datasets", methods=["POST"])
def create_dataset():
    return jsonify(registries_service.create_dataset(current_app.config["REPO_PATH"], request.json))


@registries_bp.route("/rubrics", methods=["POST"])
def create_rubric():
    return jsonify(registries_service.create_rubric(current_app.config["REPO_PATH"], request.json))


@registries_bp.route("/extractors", methods=["POST"])
def create_extractor():
    return jsonify(registries_service.create_extractor(current_app.config["REPO_PATH"], request.json))


@registries_bp.route("/gyms", methods=["POST"])
def create_gym():
    try:
        return jsonify(registries_service.create_gym(current_app.config["REPO_PATH"], request.json))
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
        return jsonify(registries_service.generate_extractor_code(data.get("description", "")))
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
