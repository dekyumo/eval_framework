from flask import Blueprint, jsonify, request, current_app

from src.eval_workbench.services import benchmark as benchmark_service
from src.eval_workbench.services.errors import ServiceError

benchmark_bp = Blueprint("benchmark", __name__)


@benchmark_bp.route("/report", methods=["POST"])
def run_report():
    data = request.json or {}
    try:
        report = benchmark_service.run_headless_benchmark(
            current_app.config["REPO_PATH"],
            data["agent_path"],
            data["commit"],
            data["dataset_name"],
            tags=data.get("tags"),
            model_id=data.get("model_id", "gemini-2.5-flash"),
            output_format=data.get("output_format", "markdown"),
            output_path=data.get("output_path"),
        )
        return jsonify({"report": report})
    except ServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except KeyError as exc:
        return jsonify({"error": f"Missing field: {exc.args[0]}"}), 400
