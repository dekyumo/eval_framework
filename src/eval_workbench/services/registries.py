from src.eval_workbench.extraction import extractor as extractor_module
from src.eval_workbench.domain.case import EvalCase, EvalDataset
from src.eval_workbench.domain.extractor import Extractor
from src.eval_workbench.domain.gym import Gym
from src.eval_workbench.domain.rubric import Rubric
from src.eval_workbench.domain.tag import Tag
from src.eval_workbench.services._conn import conn
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.storage.repositories import (
    EvalCaseRepository,
    EvalDatasetRepository,
    ExtractorRepository,
    GymRepository,
    RubricRepository,
    TagRepository,
)


def list_tags(repo_path: str) -> list[Tag]:
    """List all registry tags."""
    items = TagRepository(conn(repo_path)).get_all("Tag", "id", Tag)
    return items


def list_datasets(repo_path: str) -> list[EvalDataset]:
    """List all eval datasets."""
    items = EvalDatasetRepository(conn(repo_path)).get_all("EvalDataset", "id", EvalDataset)
    return items


def list_rubrics(repo_path: str) -> list[Rubric]:
    """List all scoring rubrics."""
    items = RubricRepository(conn(repo_path)).get_all("Rubric", "id", Rubric)
    return items


def list_extractors(repo_path: str) -> list[Extractor]:
    """List all trace extractors."""
    items = ExtractorRepository(conn(repo_path)).get_all("Extractor", "id", Extractor)
    return items


def list_gyms(repo_path: str) -> list[Gym]:
    """List gym environments for agentic-user simulations."""
    items = GymRepository(conn(repo_path)).get_all("Gym", "id", Gym)
    return items


def create_tag(repo_path: str, tag: Tag) -> Tag:
    """Create a registry tag."""
    TagRepository(conn(repo_path)).save(tag)
    return tag


def create_dataset(repo_path: str, dataset: EvalDataset) -> EvalDataset:
    """Create an eval dataset."""
    EvalDatasetRepository(conn(repo_path)).save(dataset)
    return dataset


def create_rubric(repo_path: str, rubric: Rubric) -> Rubric:
    """Create a scoring rubric."""
    RubricRepository(conn(repo_path)).save(rubric)
    return rubric


def create_extractor(repo_path: str, extractor: Extractor, *, python_code: str) -> Extractor:
    """Create a trace extractor."""
    source_path = extractor_module.save_extractor_source(repo_path, extractor.id, python_code)
    saved = extractor.model_copy(
        update={
            "source_path": source_path,
            "fingerprint": extractor_module.fingerprint_source(python_code),
        }
    )
    ExtractorRepository(conn(repo_path)).save(saved)
    return saved


def create_gym(repo_path: str, gym: Gym) -> Gym:
    """Register a gym class for agentic-user eval cases."""
    GymRepository(conn(repo_path)).save(gym)
    return gym


def delete_gym(repo_path: str, gym_id: str) -> None:
    connection = conn(repo_path)
    cases = EvalCaseRepository(connection).get_all("EvalCase", "id", EvalCase)
    in_use = any(getattr(case.agentic_user, "gym_ref", None) == gym_id for case in cases)
    if in_use:
        raise ServiceError("Gym is in use by a case and cannot be deleted", 400)
    GymRepository(connection).delete(gym_id)


def delete_tag(repo_path: str, tag_id: str) -> None:
    connection = conn(repo_path)
    query = "MATCH (c:EvalCase)-[:TAGGED]->(t:Tag {id: $id}) RETURN count(c)"
    result = connection.execute(query, {"id": tag_id})
    count = result.get_next()[0] if result.has_next() else 0
    if count > 0:
        raise ServiceError("Tag is in use by a case and cannot be deleted", 400)
    TagRepository(connection).delete(tag_id)


def delete_dataset(repo_path: str, dataset_id: str) -> None:
    connection = conn(repo_path)
    dataset = EvalDatasetRepository(connection).get(dataset_id)
    if dataset and len(dataset.case_ids) > 0:
        raise ServiceError("Dataset is not empty and cannot be deleted", 400)
    EvalDatasetRepository(connection).delete(dataset_id)


def delete_rubric(repo_path: str, rubric_id: str) -> None:
    connection = conn(repo_path)
    cases = EvalCaseRepository(connection).get_all("EvalCase", "id", EvalCase)
    in_use = any(any(metric.rubric_ref == rubric_id for metric in getattr(case, "metrics", [])) for case in cases)
    if in_use:
        raise ServiceError("Rubric is in use by a case metric and cannot be deleted", 400)
    RubricRepository(connection).delete(rubric_id)


def delete_extractor(repo_path: str, extractor_id: str) -> None:
    connection = conn(repo_path)
    cases = EvalCaseRepository(connection).get_all("EvalCase", "id", EvalCase)
    in_use = any(
        any(metric.extractor_ref == extractor_id for metric in getattr(case, "metrics", []))
        for case in cases
    )
    if in_use:
        raise ServiceError("Extractor is in use by a case metric and cannot be deleted", 400)
    ExtractorRepository(connection).delete(extractor_id)


def generate_extractor_code(description: str) -> str:
    try:
        return extractor_module.generate_extractor_code(description)
    except Exception as exc:
        raise ServiceError(str(exc), 500) from exc
