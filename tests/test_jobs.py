import time
from unittest.mock import patch

import pytest

from src.eval_workbench.domain.task import Task, TaskProgress, TaskStatus, TaskType
from src.eval_workbench.services import events
from src.eval_workbench.services import jobs as jobs_service
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.storage.kuzu_store import close_all


@pytest.fixture(autouse=True)
def reset_jobs():
    with jobs_service._registry_lock:
        jobs_service._tasks.clear()
        jobs_service._terminal_until.clear()
    while not jobs_service._work_queue.empty():
        try:
            jobs_service._work_queue.get_nowait()
        except Exception:
            break
    jobs_service.start_worker()
    yield
    with jobs_service._registry_lock:
        jobs_service._tasks.clear()
        jobs_service._terminal_until.clear()


@pytest.fixture
def repo_path(tmp_path):
    path = str(tmp_path / "agent_repo")
    (tmp_path / "agent_repo").mkdir()
    yield path
    close_all()


def _wait_for_task(task_id: str, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        task = jobs_service.get_task(task_id)
        if task is None:
            return
        if task.status in (TaskStatus.SUCCEEDED, TaskStatus.FAILED):
            return
        time.sleep(0.05)
    raise TimeoutError(f"Task {task_id} did not finish")


def test_enqueue_generate_trace_completes_and_publishes_event(repo_path):
    captured: list[tuple[str, dict]] = []
    original_publish = events.publish

    def publish_and_capture(event_type: str, data: dict) -> None:
        captured.append((event_type, data))
        original_publish(event_type, data)

    class FakeRun:
        def model_dump(self, mode="json"):
            return {
                "id": "run1",
                "snapshot_id": "snap1",
                "case_id": "case1",
                "model_id": "gemini-2.5-flash",
                "repetition_index": 0,
                "trace": {"id": "run1", "parts": []},
            }

    with (
        patch("src.eval_workbench.services.jobs.runs_service.generate_run", return_value=FakeRun()),
        patch("src.eval_workbench.services.jobs.events.publish", side_effect=publish_and_capture),
    ):
        task = jobs_service.enqueue_generate_trace(repo_path, "snap1", "case1", "gemini-2.5-flash")
        _wait_for_task(task.id)

    assert jobs_service.get_task(task.id) is not None
    assert jobs_service.get_task(task.id).status == TaskStatus.SUCCEEDED
    assert any(name == "trace_generated" for name, _ in captured)


def test_finished_tasks_remain_fetchable_then_expire(repo_path):
    stored = Task(
        id="task_test",
        type=TaskType.GENERATE_TRACE,
        status=TaskStatus.RUNNING,
        label="Test",
        progress=TaskProgress(done=0, total=1),
    )
    with jobs_service._registry_lock:
        jobs_service._tasks[stored.id] = stored
    assert len(jobs_service.list_active_tasks()) == 1
    jobs_service._finish_task(stored.id, status=TaskStatus.SUCCEEDED)
    finished = jobs_service.get_task(stored.id)
    assert finished is not None
    assert finished.status == TaskStatus.SUCCEEDED
    assert len(jobs_service.list_active_tasks()) == 0
    assert any(task.id == stored.id for task in jobs_service.list_tasks())

    with jobs_service._registry_lock:
        jobs_service._terminal_until[stored.id] = time.monotonic() - 1
    assert jobs_service.get_task(stored.id) is None
    assert jobs_service.list_tasks() == []


def test_enqueue_generate_traces_requires_dataset(repo_path):
    with pytest.raises(ServiceError):
        jobs_service.enqueue_generate_traces(repo_path, "snap1", "missing", "gemini-2.5-flash")


def test_campaign_marks_failed_when_items_fail(repo_path):
    from src.eval_workbench.domain.campaign import EvalCampaign

    campaign = EvalCampaign(
        id="camp1",
        name="Camp",
        base_snapshot_id="snap1",
        dataset_id="ds1",
        model_panel=["gemini-2.5-flash"],
        created_at=time.time(),
    )
    with patch(
        "src.eval_workbench.services.jobs.campaigns_service.save_campaign",
        return_value=campaign,
    ), patch(
        "src.eval_workbench.services.jobs.campaigns_service.execute_campaign",
        return_value={"succeeded": 0, "failed": 3, "total": 3},
    ):
        task = jobs_service.enqueue_run_campaign(repo_path, campaign)
        _wait_for_task(task.id)

    finished = jobs_service.get_task(task.id)
    assert finished is not None
    assert finished.status == TaskStatus.FAILED
    assert finished.error and "3/3" in finished.error
