import pytest
from pydantic import ValidationError

from src.eval_workbench.domain.case import EvalCase, EvalDataset
from src.eval_workbench.domain.trace import MessagePart
from src.eval_workbench.services.cases import (
    create_case,
    deactivate_case,
    get_case,
    list_cases,
    update_case,
)
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.storage.kuzu_store import close_all, get_connection
from src.eval_workbench.storage.repositories import EvalDatasetRepository


@pytest.fixture
def repo_path(tmp_path):
    path = str(tmp_path / "agent_repo")
    (tmp_path / "agent_repo").mkdir()
    yield path
    close_all()


@pytest.fixture
def seeded_dataset(repo_path):
    dataset = EvalDataset(id="ds1", name="Test Dataset", case_ids=[])
    EvalDatasetRepository(get_connection(repo_path)).save(dataset)
    return dataset


def _base_case(case_id: str = "case_v1") -> EvalCase:
    return EvalCase.model_validate({
        "id": case_id,
        "name": "Paris Budget",
        "dataset_id": "ds1",
        "conversation": [MessagePart(role="user", kind="text", text="hi")],
        "distribution_position": "in",
        "problem_type": "happy",
    })


def test_create_case_sets_logical_id_and_version(repo_path, seeded_dataset):
    saved = create_case(repo_path, _base_case())
    assert saved.logical_id == "paris_budget"
    assert saved.version == 1
    assert saved.active_for_eval is True


def test_new_version_does_not_deactivate_old(repo_path, seeded_dataset):
    v1 = create_case(repo_path, _base_case("case_v1"))
    v2 = create_case(repo_path, _base_case("case_v2"), from_version_of=v1.id)
    assert v2.logical_id == v1.logical_id
    assert v2.version == 2

    reloaded_v1 = get_case(repo_path, v1.id)
    assert reloaded_v1.active_for_eval is True


def test_update_without_runs(repo_path, seeded_dataset):
    saved = create_case(repo_path, _base_case())
    updated = update_case(repo_path, saved.model_copy(update={"name": "Paris Budget Updated"}))
    assert updated.name == "Paris Budget Updated"


def test_update_with_runs_requires_cascade(repo_path, seeded_dataset):
    from src.eval_workbench.domain.run import EvalRun
    from src.eval_workbench.domain.trace import Trace, MessagePart
    from src.eval_workbench.storage.repositories import EvalRunRepository

    saved = create_case(repo_path, _base_case())
    connection = get_connection(repo_path)
    trace = Trace(
        id="run_test_1",
        parts=[MessagePart(role="user", kind="text", text="hi")],
        snapshot_id="snap_missing",
        case_id=saved.id,
        model_id="gemini-2.5-flash",
    )
    run = EvalRun(
        id="run_test_1",
        snapshot_id="snap_missing",
        case_id=saved.id,
        model_id="gemini-2.5-flash",
        repetition_index=0,
        trace=trace,
    )
    EvalRunRepository(connection).save(run)

    with pytest.raises(ServiceError) as exc:
        update_case(repo_path, saved.model_copy(update={"name": "Changed"}))
    assert exc.value.status_code == 409

    updated = update_case(
        repo_path,
        saved.model_copy(update={"name": "Changed"}),
        cascade=True,
    )
    assert updated.name == "Changed"


def test_cascade_update_invalid_payload_preserves_runs(repo_path, seeded_dataset):
    from src.eval_workbench.domain.run import EvalRun
    from src.eval_workbench.domain.trace import Trace, MessagePart
    from src.eval_workbench.storage.repositories import EvalRunRepository

    saved = create_case(repo_path, _base_case())
    connection = get_connection(repo_path)
    trace = Trace(
        id="run_test_1",
        parts=[MessagePart(role="user", kind="text", text="hi")],
        snapshot_id="snap_missing",
        case_id=saved.id,
        model_id="gemini-2.5-flash",
    )
    run = EvalRun(
        id="run_test_1",
        snapshot_id="snap_missing",
        case_id=saved.id,
        model_id="gemini-2.5-flash",
        repetition_index=0,
        trace=trace,
    )
    EvalRunRepository(connection).save(run)

    with pytest.raises(ValidationError):
        update_case(
            repo_path,
            saved.model_copy(update={"version": "not-a-version"}),
            cascade=True,
        )

    assert len(EvalRunRepository(connection).list_by_case(saved.id)) == 1
    assert get_case(repo_path, saved.id).name == saved.name


def test_deactivate_and_active_only_list(repo_path, seeded_dataset):
    saved = create_case(repo_path, _base_case())
    deactivate_case(repo_path, saved.id)

    inactive = get_case(repo_path, saved.id)
    assert inactive.active_for_eval is False

    all_cases = list_cases(repo_path)
    active_cases = list_cases(repo_path, active_only=True)
    assert len(all_cases) == 1
    assert len(active_cases) == 0
