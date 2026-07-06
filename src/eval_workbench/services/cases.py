from src.eval_workbench.domain.case import EvalCase
from src.eval_workbench.services._conn import conn
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.storage.repositories import EvalCaseRepository, EvalDatasetRepository, SnapshotRepository
from src.eval_workbench.agents.case_writer.case_writer_runner import generate_eval_case


def list_cases(repo_path: str) -> list[dict]:
    repository = EvalCaseRepository(conn(repo_path))
    cases = repository.get_all("EvalCase", "id", EvalCase)
    return [case.model_dump() for case in cases]


def create_case(repo_path: str, data: dict, dataset_id: str | None = None) -> dict:
    payload = dict(data)
    payload.pop("repo_path", None)
    payload.pop("dataset_id", None)

    if payload.get("input_payload") and payload.get("conversation"):
        raise ServiceError("Use either conversation turns or input_payload, not both", 400)

    case = EvalCase(**payload)
    connection = conn(repo_path)
    EvalCaseRepository(connection).save(case)

    if dataset_id:
        dataset = EvalDatasetRepository(connection).get(dataset_id)
        if dataset and case.id not in dataset.case_ids:
            dataset.case_ids.append(case.id)
            EvalDatasetRepository(connection).save(dataset)

    return case.model_dump()


def get_case(repo_path: str, case_id: str) -> dict | None:
    case = EvalCaseRepository(conn(repo_path)).get(case_id)
    if not case:
        return None
    return case.model_dump()


def generate_case(repo_path: str, snapshot_id: str, specification: str) -> dict:
    if not snapshot_id:
        raise ServiceError("snapshot_id is required", 400)
    if not specification or not specification.strip():
        raise ServiceError("specification is required", 400)

    snapshot = SnapshotRepository(conn(repo_path)).get(snapshot_id)
    if not snapshot:
        raise ServiceError("Snapshot not found", 404)

    try:
        return generate_eval_case(snapshot, specification.strip())
    except ServiceError:
        raise
    except Exception as exc:
        raise ServiceError(str(exc), 500) from exc
