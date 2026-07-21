import pytest

from src.eval_workbench.services import jobs as jobs_service


@pytest.fixture
def repo_path(tmp_path):
    path = str(tmp_path / "agent_repo")
    (tmp_path / "agent_repo").mkdir()
    return path


def test_list_jobs_empty(client):
    response = client.get("/api/jobs/")
    assert response.status_code == 200
    assert response.get_json() == []


def test_events_stream_connects(client):
    with client.get("/api/jobs/events") as response:
        assert response.status_code == 200
        assert response.mimetype == "text/event-stream"
        first_chunk = next(response.response)
        assert b": connected" in first_chunk


def test_enqueue_generate_trace_returns_202(client, repo_path):
    from unittest.mock import patch

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

    client.application.config["REPO_PATH"] = repo_path
    with patch("src.eval_workbench.services.jobs.runs_service.generate_run", return_value=FakeRun()):
        response = client.post(
            "/api/jobs/generate-trace",
            json={
                "snapshot_id": "snap1",
                "case_id": "case1",
                "model_id": "gemini-2.5-flash",
            },
        )
    assert response.status_code == 202
    body = response.get_json()
    assert body["task_id"]
    assert body["task"]["type"] == "generate_trace"
