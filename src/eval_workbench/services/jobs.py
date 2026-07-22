"""In-memory background job queue for the web GUI.

Designed for a single Flask process (`threaded=True`). Task state and the worker
queue are process-local — do not run multi-worker WSGI without an external broker.
"""

from __future__ import annotations

import queue
import threading
import time
import uuid
from collections.abc import Callable

from src.eval_workbench.domain.campaign import EvalCampaign
from src.eval_workbench.domain.case import EvalDataset
from src.eval_workbench.domain.snapshot import AgentTarget
from src.eval_workbench.domain.task import Task, TaskProgress, TaskStatus, TaskType
from src.eval_workbench.services import campaigns as campaigns_service
from src.eval_workbench.services import events
from src.eval_workbench.services import runs as runs_service
from src.eval_workbench.services._conn import conn
from src.eval_workbench.services import agents as agents_service
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.storage.repositories import EvalCaseRepository, EvalDatasetRepository

# How long finished tasks remain fetchable so SSE reconnect / focus refresh
# can recover success/failure (and error text) after a missed event.
_TERMINAL_RETENTION_S = 60.0

_tasks: dict[str, Task] = {}
_terminal_until: dict[str, float] = {}
_registry_lock = threading.Lock()
_work_queue: queue.Queue[Callable[[], None]] = queue.Queue()
_worker_lock = threading.Lock()
_worker_started = False


def _new_task_id() -> str:
    return f"task_{uuid.uuid4().hex[:12]}"


def _publish_task(task: Task) -> None:
    events.publish("task_updated", task.model_dump(mode="json"))


def _purge_expired_terminal() -> None:
    now = time.monotonic()
    with _registry_lock:
        expired = [tid for tid, until in _terminal_until.items() if now >= until]
        for tid in expired:
            _tasks.pop(tid, None)
            _terminal_until.pop(tid, None)


def _remove_task(task_id: str) -> None:
    with _registry_lock:
        _tasks.pop(task_id, None)
        _terminal_until.pop(task_id, None)


def _get_task(task_id: str) -> Task | None:
    _purge_expired_terminal()
    with _registry_lock:
        return _tasks.get(task_id)


def _store_task(task: Task) -> None:
    with _registry_lock:
        _tasks[task.id] = task
        _terminal_until.pop(task.id, None)
    _publish_task(task)


def _finish_task(task_id: str, *, status: TaskStatus, error: str | None = None) -> None:
    task = _get_task(task_id)
    if not task:
        return
    finished = task.model_copy(update={"status": status, "error": error})
    with _registry_lock:
        _tasks[task_id] = finished
        _terminal_until[task_id] = time.monotonic() + _TERMINAL_RETENTION_S
    _publish_task(finished)


def _set_running(task_id: str) -> None:
    task = _get_task(task_id)
    if not task:
        return
    _store_task(task.model_copy(update={"status": TaskStatus.RUNNING}))


def _set_progress(task_id: str, done: int, total: int) -> None:
    task = _get_task(task_id)
    if not task:
        return
    _store_task(task.model_copy(update={"progress": TaskProgress(done=done, total=total)}))


def list_tasks() -> list[Task]:
    """Return active tasks plus recently finished ones (within retention)."""
    _purge_expired_terminal()
    with _registry_lock:
        return list(_tasks.values())


def list_active_tasks() -> list[Task]:
    """Return only queued/running tasks."""
    return [
        task
        for task in list_tasks()
        if task.status in (TaskStatus.QUEUED, TaskStatus.RUNNING)
    ]


def get_task(task_id: str) -> Task | None:
    return _get_task(task_id)


def start_worker() -> None:
    global _worker_started
    with _worker_lock:
        if _worker_started:
            return
        _worker_started = True
        thread = threading.Thread(target=_worker_loop, daemon=True, name="eval-job-worker")
        thread.start()


def _worker_loop() -> None:
    while True:
        work = _work_queue.get()
        try:
            work()
        except Exception as exc:
            print(f"Job worker error: {exc}")
        finally:
            _work_queue.task_done()


def _enqueue(task: Task, work: Callable[[], None]) -> Task:
    _store_task(task)
    _work_queue.put(work)
    return task


def _dataset_cases(repo_path: str, dataset_id: str) -> tuple[EvalDataset, list[str], str]:
    connection = conn(repo_path)
    dataset = EvalDatasetRepository(connection).get(dataset_id)
    if not dataset:
        raise ServiceError(f"Dataset not found: {dataset_id}", 404)
    case_repo = EvalCaseRepository(connection)
    case_ids: list[str] = []
    for case_id in dataset.case_ids or []:
        case = case_repo.get(case_id)
        if case and case.active_for_eval:
            case_ids.append(case_id)
    return dataset, case_ids, dataset.name or dataset.id


def enqueue_generate_traces(
    repo_path: str,
    snapshot_id: str,
    dataset_id: str,
    model_id: str,
    *,
    force: bool = False,
) -> Task:
    dataset, case_ids, dataset_name = _dataset_cases(repo_path, dataset_id)
    total = len(case_ids)
    task_id = _new_task_id()
    task = Task(
        id=task_id,
        type=TaskType.GENERATE_TRACES,
        status=TaskStatus.QUEUED,
        label=f"Generate traces · {dataset_name}",
        progress=TaskProgress(done=0, total=total),
    )

    def work() -> None:
        _set_running(task_id)
        try:
            for index, case_id in enumerate(case_ids, start=1):
                run = runs_service.generate_run(
                    repo_path,
                    snapshot_id,
                    case_id,
                    model_id,
                    force=force,
                )
                events.publish(
                    "trace_generated",
                    {
                        "task_id": task_id,
                        "snapshot_id": snapshot_id,
                        "case_id": case_id,
                        "run": run.model_dump(mode="json"),
                    },
                )
                _set_progress(task_id, index, total)
            _finish_task(task_id, status=TaskStatus.SUCCEEDED)
        except Exception as exc:
            _finish_task(task_id, status=TaskStatus.FAILED, error=str(exc))

    return _enqueue(task, work)


def enqueue_generate_trace(
    repo_path: str,
    snapshot_id: str,
    case_id: str,
    model_id: str,
    *,
    force: bool = False,
) -> Task:
    connection = conn(repo_path)
    case = EvalCaseRepository(connection).get(case_id)
    case_name = (case.name if case else None) or case_id
    task_id = _new_task_id()
    task = Task(
        id=task_id,
        type=TaskType.GENERATE_TRACE,
        status=TaskStatus.QUEUED,
        label=f"Generate trace · {case_name}",
        progress=TaskProgress(done=0, total=1),
    )

    def work() -> None:
        _set_running(task_id)
        try:
            run = runs_service.generate_run(
                repo_path,
                snapshot_id,
                case_id,
                model_id,
                force=force,
            )
            events.publish(
                "trace_generated",
                {
                    "task_id": task_id,
                    "snapshot_id": snapshot_id,
                    "case_id": case_id,
                    "run": run.model_dump(mode="json"),
                },
            )
            _set_progress(task_id, 1, 1)
            _finish_task(task_id, status=TaskStatus.SUCCEEDED)
        except Exception as exc:
            _finish_task(task_id, status=TaskStatus.FAILED, error=str(exc))

    return _enqueue(task, work)


def enqueue_evaluate_traces(
    repo_path: str,
    snapshot_id: str,
    dataset_id: str,
    *,
    force: bool = False,
) -> Task:
    dataset, case_ids, dataset_name = _dataset_cases(repo_path, dataset_id)
    runs = runs_service.list_runs(repo_path)
    scored_run_ids = {item.run_id for item in runs_service.list_scored_runs(repo_path)}
    active_case_ids = set(case_ids)
    runs_to_score = [
        run
        for run in runs
        if run.snapshot_id == snapshot_id
        and run.case_id in active_case_ids
        and (force or run.id not in scored_run_ids)
    ]
    total = len(runs_to_score)
    task_id = _new_task_id()
    task = Task(
        id=task_id,
        type=TaskType.EVALUATE_TRACES,
        status=TaskStatus.QUEUED,
        label=f"Evaluate traces · {dataset_name}",
        progress=TaskProgress(done=0, total=total),
    )

    def work() -> None:
        _set_running(task_id)
        try:
            for index, run in enumerate(runs_to_score, start=1):
                scored_run = runs_service.evaluate_run(repo_path, run.id, force=force)
                events.publish(
                    "trace_evaluated",
                    {
                        "task_id": task_id,
                        "run_id": run.id,
                        "scored": scored_run.model_dump(mode="json"),
                    },
                )
                _set_progress(task_id, index, total)
            _finish_task(task_id, status=TaskStatus.SUCCEEDED)
        except Exception as exc:
            _finish_task(task_id, status=TaskStatus.FAILED, error=str(exc))

    return _enqueue(task, work)


def enqueue_evaluate_trace(repo_path: str, run_id: str, *, force: bool = False) -> Task:
    task_id = _new_task_id()
    task = Task(
        id=task_id,
        type=TaskType.EVALUATE_TRACE,
        status=TaskStatus.QUEUED,
        label=f"Evaluate trace · {run_id}",
        progress=TaskProgress(done=0, total=1),
    )

    def work() -> None:
        _set_running(task_id)
        try:
            scored_run = runs_service.evaluate_run(repo_path, run_id, force=force)
            events.publish(
                "trace_evaluated",
                {
                    "task_id": task_id,
                    "run_id": run_id,
                    "scored": scored_run.model_dump(mode="json"),
                },
            )
            _set_progress(task_id, 1, 1)
            _finish_task(task_id, status=TaskStatus.SUCCEEDED)
        except Exception as exc:
            _finish_task(task_id, status=TaskStatus.FAILED, error=str(exc))

    return _enqueue(task, work)


def enqueue_run_campaign(repo_path: str, campaign: EvalCampaign) -> Task:
    campaigns_service.save_campaign(repo_path, campaign)
    task_id = _new_task_id()
    task = Task(
        id=task_id,
        type=TaskType.RUN_CAMPAIGN,
        status=TaskStatus.QUEUED,
        label=f"Campaign · {campaign.name}",
        progress=TaskProgress(done=0, total=0),
    )

    def work() -> None:
        _set_running(task_id)

        def on_progress(done: int, total: int) -> None:
            _set_progress(task_id, done, total)

        try:
            summary = campaigns_service.execute_campaign(
                repo_path,
                campaign.id,
                on_progress=on_progress,
            )
            events.publish(
                "campaign_finished",
                {
                    "task_id": task_id,
                    "campaign_id": campaign.id,
                    "summary": summary,
                },
            )
            failed = int(summary.get("failed", 0))
            total = int(summary.get("total", 0))
            if failed > 0:
                _finish_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    error=f"Campaign finished with {failed}/{total} failed items",
                )
            else:
                _finish_task(task_id, status=TaskStatus.SUCCEEDED)
        except Exception as exc:
            _finish_task(task_id, status=TaskStatus.FAILED, error=str(exc))

    return _enqueue(task, work)


def enqueue_scan_agent(repo_path: str, target: AgentTarget, commit: str) -> Task:
    agent_label = target.agent_path.split(":")[-1] if target.agent_path else "agent"
    task_id = _new_task_id()
    task = Task(
        id=task_id,
        type=TaskType.SCAN_AGENT,
        status=TaskStatus.QUEUED,
        label=f"Scan agent · {agent_label}",
        progress=TaskProgress(done=0, total=1),
    )

    def work() -> None:
        _set_running(task_id)
        try:
            snapshot = agents_service.scan(repo_path, target, commit)
            events.publish(
                "snapshot_scanned",
                {
                    "task_id": task_id,
                    "snapshot": snapshot.model_dump(mode="json"),
                },
            )
            _set_progress(task_id, 1, 1)
            _finish_task(task_id, status=TaskStatus.SUCCEEDED)
        except Exception as exc:
            _finish_task(task_id, status=TaskStatus.FAILED, error=str(exc))

    return _enqueue(task, work)
