from src.eval_workbench.domain.case import EvalCase, EvalDataset
from src.eval_workbench.domain.run import EvalRun, ScoredEvalRun
from src.eval_workbench.runner.agent_runner import AgentRunner
from src.eval_workbench.services._conn import conn
from src.eval_workbench.services._ids import build_run_id
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.services.scoring import score_trace
from src.eval_workbench.storage.repositories import (
    EvalCaseRepository,
    EvalDatasetRepository,
    EvalRunRepository,
    ScoredEvalRunRepository,
    SnapshotRepository,
)


def _dataset_name_for_case(connection, case_id: str) -> str:
    datasets = EvalDatasetRepository(connection).get_all("EvalDataset", "id", EvalDataset)
    for dataset in datasets:
        if case_id in (dataset.case_ids or []):
            return dataset.name or dataset.id
    return "UnknownDataset"


def find_existing_run(
    connection,
    snapshot_id: str,
    case_id: str,
    model_id: str,
    repetition_index: int = 0,
) -> EvalRun | None:
    return EvalRunRepository(connection).find_by_snapshot_case(
        snapshot_id, case_id, model_id, repetition_index
    )


def _delete_scored_for_run(connection, run_id: str) -> None:
    scored_repo = ScoredEvalRunRepository(connection)
    scored_id = f"scored_{run_id}"
    if scored_repo.get(scored_id):
        scored_repo._delete_node("ScoredEvalRun", "id", scored_id)


def generate_run(
    repo_path: str,
    snapshot_id: str,
    case_id: str,
    model_id: str,
    *,
    force: bool = False,
) -> dict:
    connection = conn(repo_path)
    snapshot = SnapshotRepository(connection).get(snapshot_id)
    case = EvalCaseRepository(connection).get(case_id)

    if not snapshot or not case:
        raise ServiceError("Snapshot or case not found", 404)

    if not case.active_for_eval:
        raise ServiceError("Case is inactive for eval", 400)

    existing = find_existing_run(connection, snapshot_id, case_id, model_id)
    if existing and not force:
        return existing.model_dump()

    try:
        trace = AgentRunner(snapshot).run_case(case, model_id)
        dataset_name = _dataset_name_for_case(connection, case_id)
        agent_name = snapshot.agent_target.agent_path.split(":")[-1]

        if existing and force:
            run_id = existing.id
            _delete_scored_for_run(connection, run_id)
        else:
            run_id = build_run_id(
                dataset_name=dataset_name,
                case_name=case.name or case.id,
                agent_name=agent_name,
                commit_hash=snapshot.commit_hash or "",
                model_id=model_id,
                trace_id=trace.id,
            )

        trace.id = run_id
        run = EvalRun(
            id=run_id,
            snapshot_id=snapshot_id,
            case_id=case_id,
            model_id=model_id,
            repetition_index=0,
            trace=trace,
        )
        EvalRunRepository(connection).save(run)
        return run.model_dump()
    except ServiceError:
        raise
    except Exception as exc:
        raise ServiceError(str(exc), 500) from exc


def list_runs(repo_path: str) -> list[dict]:
    runs = EvalRunRepository(conn(repo_path)).get_all("EvalRun", "id", EvalRun)
    return [run.model_dump() for run in runs]


def list_scored_runs(repo_path: str) -> list[dict]:
    runs = ScoredEvalRunRepository(conn(repo_path)).get_all("ScoredEvalRun", "id", ScoredEvalRun)
    return [run.model_dump() for run in runs]


def evaluate_run(repo_path: str, run_id: str, *, force: bool = False) -> dict:
    connection = conn(repo_path)
    run = EvalRunRepository(connection).get(run_id)
    if not run:
        raise ServiceError("Run not found", 404)

    scored_id = f"scored_{run_id}"
    existing = ScoredEvalRunRepository(connection).get(scored_id)
    if existing and not force:
        return existing.model_dump()

    case = EvalCaseRepository(connection).get(run.case_id)
    if not case:
        raise ServiceError("Case not found", 404)

    try:
        results = score_trace(run.trace, case, connection)
        scored = ScoredEvalRun(
            id=scored_id,
            run_id=run_id,
            results=results,
        )
        ScoredEvalRunRepository(connection).save(scored)
        return scored.model_dump()
    except ServiceError:
        raise
    except Exception as exc:
        raise ServiceError(str(exc), 500) from exc
