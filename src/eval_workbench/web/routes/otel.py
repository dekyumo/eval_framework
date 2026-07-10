import json
import os
import time

from flask import Blueprint, Response, current_app, request

otel_bp = Blueprint("otel", __name__)


def _otel_dump_dir(subdir: str = "") -> str:
    base = current_app.config.get("OTEL_TRACE_DUMP_PATH")
    if not base:
        base = os.path.join(current_app.config["REPO_PATH"], "raw_otel_logs")
    dump_path = os.path.join(base, subdir) if subdir else base
    os.makedirs(dump_path, exist_ok=True)
    return dump_path


def _save_otel_export(request_type: str, subdir: str) -> Response:
    from google.protobuf.json_format import MessageToDict

    if request_type == "traces":
        from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
        export = ExportTraceServiceRequest()
    elif request_type == "metrics":
        from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import ExportMetricsServiceRequest
        export = ExportMetricsServiceRequest()
    else:
        from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
        export = ExportLogsServiceRequest()

    export.ParseFromString(request.get_data())
    dump = MessageToDict(export)
    filename = os.path.join(_otel_dump_dir(subdir), f"{time.time_ns()}.json")
    with open(filename, "w", encoding="utf-8") as handle:
        json.dump(dump, handle, indent=2)

    return Response(status=200)


@otel_bp.post("/v1/traces")
def save_traces():
    return _save_otel_export("traces", "traces")


@otel_bp.post("/v1/logs")
def save_logs():
    return _save_otel_export("logs", "logs")

@otel_bp.post("/v1/metrics")
def save_metrics():
    return _save_otel_export("metrics", "metrics")
