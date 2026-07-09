import os


def configure_otel_export(host: str, port: int, service_name: str = "eval-workbench-agent") -> str:
    """Point ADK/OpenTelemetry exporters at this workbench's OTLP HTTP receiver."""
    endpoint = f"http://{host}:{port}"
    os.environ["OTEL_SERVICE_NAME"] = service_name
    os.environ["OTEL_TRACES_EXPORTER"] = "otlp"
    os.environ["OTEL_EXPORTER_OTLP_PROTOCOL"] = "http/protobuf"
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint
    os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{endpoint}/v1/traces"
    os.environ["OTEL_LOGS_EXPORTER"] = "otlp"
    os.environ["OTEL_EXPORTER_OTLP_LOGS_ENDPOINT"] = f"{endpoint}/v1/logs"
    return endpoint
