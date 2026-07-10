import os

import pytest

from src.eval_workbench.web.app import create_app


def test_configure_otel_export_sets_env(monkeypatch):
    from src.eval_workbench.otel_config import configure_otel_export

    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    endpoint = configure_otel_export("127.0.0.1", 5000)
    assert endpoint == "http://127.0.0.1:5000"
    assert os.environ["OTEL_TRACES_EXPORTER"] == "otlp"
    assert os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://127.0.0.1:5000"
    assert os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] == "http://127.0.0.1:5000/v1/traces"
    assert os.environ["OTEL_EXPORTER_OTLP_LOGS_ENDPOINT"] == "http://127.0.0.1:5000/v1/logs"


def test_otel_endpoint_not_registered_by_default():
    app = create_app()
    client = app.test_client()
    response = client.post("/v1/traces", data=b"", content_type="application/x-protobuf")
    assert response.status_code in (404, 405)


def test_otel_trace_dump_endpoint(tmp_path):
    pytest.importorskip("opentelemetry.proto")
    from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest

    dump_dir = tmp_path / "raw_otel_logs"
    app = create_app(
        repo_path=str(tmp_path),
        log_raw_otel=True,
        otel_trace_dump_path=str(dump_dir),
    )
    client = app.test_client()

    payload = ExportTraceServiceRequest().SerializeToString()
    response = client.post("/v1/traces", data=payload, content_type="application/x-protobuf")

    assert response.status_code == 200
    files = list((dump_dir / "traces").glob("*.json"))
    assert len(files) == 1
    assert files[0].read_text(encoding="utf-8").startswith("{")


def test_otel_logs_dump_endpoint(tmp_path):
    pytest.importorskip("opentelemetry.proto")
    from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest

    dump_dir = tmp_path / "raw_otel_logs"
    app = create_app(
        repo_path=str(tmp_path),
        log_raw_otel=True,
        otel_trace_dump_path=str(dump_dir),
    )
    client = app.test_client()

    payload = ExportLogsServiceRequest().SerializeToString()
    response = client.post("/v1/logs", data=payload, content_type="application/x-protobuf")

    assert response.status_code == 200
    files = list((dump_dir / "logs").glob("*.json"))
    assert len(files) == 1
