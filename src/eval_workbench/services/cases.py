import re

from src.eval_workbench.domain.case import EvalCase, EvalDataset
from src.eval_workbench.services._conn import conn
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.storage.kuzu_store import kuzu_transaction
from src.eval_workbench.storage.repositories import (
    EvalCaseRepository,
    EvalDatasetRepository,
    EvalRunRepository,
    SnapshotRepository,
)
from src.eval_workbench.agents.case_writer.case_writer_runner import generate_eval_case


def _slug_logical_id(name: str, case_id: str) -> str:
    base = (name or case_id).strip().lower()
    slug = re.sub(r"[^a-z0-9_-]+", "_", base).strip("_")
    return slug or case_id


def _normalize_case(case: EvalCase) -> EvalCase:
    logical_id = case.logical_id or _slug_logical_id(case.name, case.id)
    version = case.version if case.version and case.version >= 1 else 1
    active = case.active_for_eval if case.active_for_eval is not None else True
    if logical_id == case.logical_id and version == case.version and active == case.active_for_eval:
        return case
    return case.model_copy(update={"logical_id": logical_id, "version": version, "active_for_eval": active})


def cases_eligible_for_dataset(connection, dataset: EvalDataset) -> list[EvalCase]:
    repository = EvalCaseRepository(connection)
    cases: list[EvalCase] = []
    for case_id in dict.fromkeys(dataset.case_ids or []):
        case = repository.get(case_id)
        if not case:
            continue
        case = _normalize_case(case)
        if case.active_for_eval:
            cases.append(case)
    return cases


def list_cases(repo_path: str, *, active_only: bool = False) -> list[dict]:
    repository = EvalCaseRepository(conn(repo_path))
    cases = [_normalize_case(case) for case in repository.get_all("EvalCase", "id", EvalCase)]
    if active_only:
        cases = [case for case in cases if case.active_for_eval]
    return [case.model_dump() for case in cases]


def get_case_impact(repo_path: str, case_id: str) -> dict:
    connection = conn(repo_path)
    case = EvalCaseRepository(connection).get(case_id)
    if not case:
        raise ServiceError("Case not found", 404)
    return EvalCaseRepository(connection).count_run_impact(case_id)


def create_case(repo_path: str, data: dict, dataset_id: str | None = None) -> dict:
    payload = dict(data)
    payload.pop("repo_path", None)
    from_version_of = payload.pop("from_version_of", None)

    resolved_dataset_id = payload.pop("dataset_id", None) or dataset_id
    if not resolved_dataset_id or not str(resolved_dataset_id).strip():
        raise ServiceError("dataset_id is required", 400)

    if payload.get("input_payload") and payload.get("conversation"):
        raise ServiceError("Use either conversation turns or input_payload, not both", 400)

    connection = conn(repo_path)
    case_repo = EvalCaseRepository(connection)
    dataset = EvalDatasetRepository(connection).get(resolved_dataset_id)
    if not dataset:
        raise ServiceError(f"Dataset not found: {resolved_dataset_id}", 404)

    case_id = payload.get("id")
    if not case_id:
        raise ServiceError("id is required", 400)

    if from_version_of:
        source = case_repo.get(from_version_of)
        if not source:
            raise ServiceError(f"Source case not found: {from_version_of}", 404)
        source = _normalize_case(source)
        logical_id = source.logical_id
        payload["logical_id"] = logical_id
        payload["version"] = case_repo.max_version(logical_id) + 1
        payload.setdefault("active_for_eval", True)
    else:
        payload.setdefault("logical_id", _slug_logical_id(payload.get("name", ""), case_id))
        payload.setdefault("version", 1)
        payload.setdefault("active_for_eval", True)

    case = EvalCase(**payload, dataset_id=resolved_dataset_id)
    case = _normalize_case(case)
    case_repo.save(case)

    if case.id not in dataset.case_ids:
        dataset.case_ids.append(case.id)
        EvalDatasetRepository(connection).save(dataset)

    return case.model_dump()


def update_case(repo_path: str, case_id: str, data: dict, *, cascade: bool = False) -> dict:
    connection = conn(repo_path)
    case_repo = EvalCaseRepository(connection)
    existing = case_repo.get(case_id)
    if not existing:
        raise ServiceError("Case not found", 404)

    existing = _normalize_case(existing)
    impact = case_repo.count_run_impact(case_id)
    if impact["run_count"] > 0 and not cascade:
        raise ServiceError(
            "Case has existing runs; confirm force modify with cascade=true",
            409,
        )

    payload = dict(data)
    payload.pop("repo_path", None)
    payload.pop("id", None)
    payload.pop("from_version_of", None)

    if payload.get("input_payload") and payload.get("conversation"):
        raise ServiceError("Use either conversation turns or input_payload, not both", 400)

    merged = existing.model_dump()
    merged.update(payload)
    merged["id"] = case_id
    merged.setdefault("logical_id", existing.logical_id)
    merged.setdefault("version", existing.version)
    merged.setdefault("active_for_eval", existing.active_for_eval)

    case = _normalize_case(EvalCase(**merged))

    if cascade and impact["run_count"] > 0:
        with kuzu_transaction(connection):
            EvalRunRepository(connection).delete_runs_for_case(case_id)
            case_repo.save(case)
    else:
        case_repo.save(case)

    return case.model_dump()


def deactivate_case(repo_path: str, case_id: str) -> dict:
    connection = conn(repo_path)
    case_repo = EvalCaseRepository(connection)
    case = case_repo.get(case_id)
    if not case:
        raise ServiceError("Case not found", 404)
    case = _normalize_case(case).model_copy(update={"active_for_eval": False})
    case_repo.save(case)
    return case.model_dump()


def get_case(repo_path: str, case_id: str) -> dict | None:
    case = EvalCaseRepository(conn(repo_path)).get(case_id)
    if not case:
        return None
    return _normalize_case(case).model_dump()


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
