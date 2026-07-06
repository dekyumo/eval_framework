import pytest

from src.eval_workbench.domain.case import EvalCase
from src.eval_workbench.domain.trace import MessagePart
from src.eval_workbench.services.cases import create_case
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.storage.kuzu_store import close_all, get_connection
from src.eval_workbench.storage.repositories import EvalCaseRepository


@pytest.fixture
def repo_path(tmp_path):
    path = str(tmp_path / "agent_repo")
    (tmp_path / "agent_repo").mkdir()
    yield path
    close_all()


def test_create_case_persists_session_state_and_input_payload(repo_path):
    case_data = {
        "id": "case_state_1",
        "name": "State injection case",
        "target_agent_path": "agent:root",
        "conversation": [],
        "session_state": {"destination": "Acapulco", "user:name": "John Smith"},
        "input_payload": {"destination": "Acapulco"},
        "distribution_position": "in",
        "problem_type": "happy",
    }
    saved = create_case(repo_path, case_data)
    assert saved["session_state"]["destination"] == "Acapulco"
    assert saved["input_payload"]["destination"] == "Acapulco"

    loaded = EvalCaseRepository(get_connection(repo_path)).get("case_state_1")
    assert loaded is not None
    assert loaded.session_state == case_data["session_state"]
    assert loaded.input_payload == case_data["input_payload"]


def test_create_case_rejects_turns_and_payload_together(repo_path):
    with pytest.raises(ServiceError) as exc:
        create_case(
            repo_path,
            {
                "id": "case_bad",
                "target_agent_path": "agent:root",
                "conversation": [MessagePart(role="user", kind="text", text="hi").model_dump()],
                "input_payload": {"destination": "Paris"},
                "distribution_position": "in",
                "problem_type": "happy",
            },
        )
    assert exc.value.status_code == 400
