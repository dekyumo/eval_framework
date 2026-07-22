import json
import queue

from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context
from pydantic import ValidationError

from src.eval_workbench.domain.campaign import EvalCampaign
from src.eval_workbench.domain.snapshot import AgentTarget
from src.eval_workbench.services import events
from src.eval_workbench.services import jobs as jobs_service
from src.eval_workbench.services.errors import ServiceError

jobs_bp = Blueprint("jobs", __name__)


def _accepted(task):
    return jsonify({"task_id": task.id, "task": task.model_dump(mode="json")}), 202


@jobs_bp.route("/", methods=["GET"])
def list_jobs():
    return jsonify([task.model_dump(mode="json") for task in jobs_service.list_tasks()])


@jobs_bp.route("/<task_id>", methods=["GET"])
def get_job(task_id: str):
    task = jobs_service.get_task(task_id)
    if not task:
        return jsonify({"error": "not found"}), 404
    return jsonify(task.model_dump(mode="json"))


@jobs_bp.route("/events", methods=["GET"])
def event_stream():
    def generate():
        subscriber = events.subscribe()
        try:
            yield ": connected\n\n"
            while True:
                try:
                    message = subscriber.get(timeout=30)
                except queue.Empty:
                    yield ": heartbeat\n\n"
                    continue
                yield (
                    f"event: {message['type']}\n"
                    f"data: {json.dumps(message['data'])}\n\n"
                )
        finally:
            events.unsubscribe(subscriber)

    response = Response(stream_with_context(generate()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


@jobs_bp.route("/generate-traces", methods=["POST"])
def enqueue_generate_traces():
    data = request.json or {}
    try:
        task = jobs_service.enqueue_generate_traces(
            current_app.config["REPO_PATH"],
            data.get("snapshot_id"),
            data.get("dataset_id"),
            data.get("model_id"),
            force=bool(data.get("force", False)),
        )
        return _accepted(task)
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@jobs_bp.route("/generate-trace", methods=["POST"])
def enqueue_generate_trace():
    data = request.json or {}
    try:
        task = jobs_service.enqueue_generate_trace(
            current_app.config["REPO_PATH"],
            data.get("snapshot_id"),
            data.get("case_id"),
            data.get("model_id"),
            force=bool(data.get("force", False)),
        )
        return _accepted(task)
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@jobs_bp.route("/evaluate-traces", methods=["POST"])
def enqueue_evaluate_traces():
    data = request.json or {}
    try:
        task = jobs_service.enqueue_evaluate_traces(
            current_app.config["REPO_PATH"],
            data.get("snapshot_id"),
            data.get("dataset_id"),
            force=bool(data.get("force", False)),
        )
        return _accepted(task)
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@jobs_bp.route("/evaluate-trace", methods=["POST"])
def enqueue_evaluate_trace():
    data = request.json or {}
    try:
        task = jobs_service.enqueue_evaluate_trace(
            current_app.config["REPO_PATH"],
            data.get("run_id"),
            force=bool(data.get("force", False)),
        )
        return _accepted(task)
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@jobs_bp.route("/run-campaign", methods=["POST"])
def enqueue_run_campaign():
    try:
        campaign = EvalCampaign.model_validate(request.json or {})
        task = jobs_service.enqueue_run_campaign(current_app.config["REPO_PATH"], campaign)
        return _accepted(task)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@jobs_bp.route("/scan-agent", methods=["POST"])
def enqueue_scan_agent():
    data = request.json or {}
    try:
        target = AgentTarget.model_validate(
            {**data["agent_target"], "repo_path": current_app.config["REPO_PATH"]}
        )
        task = jobs_service.enqueue_scan_agent(
            current_app.config["REPO_PATH"],
            target,
            data["commit"],
        )
        return _accepted(task)
    except (KeyError, ValidationError) as exc:
        return jsonify({"error": str(exc)}), 400
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
