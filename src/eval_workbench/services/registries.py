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


def list_tags(repo_path: str) -> list[dict]:
    items = TagRepository(conn(repo_path)).get_all("Tag", "id", Tag)
    return [item.model_dump() for item in items]


def list_datasets(repo_path: str) -> list[dict]:
    items = EvalDatasetRepository(conn(repo_path)).get_all("EvalDataset", "id", EvalDataset)
    return [item.model_dump() for item in items]


def _rubric_to_api(rubric: Rubric) -> dict:
    data = rubric.model_dump()
    for item in data.get("items", []):
        item["description"] = item.get("prompt", "")
    return data


def list_rubrics(repo_path: str) -> list[dict]:
    items = RubricRepository(conn(repo_path)).get_all("Rubric", "id", Rubric)
    return [_rubric_to_api(item) for item in items]


def list_extractors(repo_path: str) -> list[dict]:
    items = ExtractorRepository(conn(repo_path)).get_all("Extractor", "id", Extractor)
    return [item.model_dump() for item in items]


def list_gyms(repo_path: str) -> list[dict]:
    items = GymRepository(conn(repo_path)).get_all("Gym", "id", Gym)
    return [item.model_dump() for item in items]


def create_tag(repo_path: str, data: dict) -> dict:
    payload = dict(data)
    payload.pop("repo_path", None)
    if not payload.get("id"):
        payload["id"] = payload.get("name", "").strip().lower().replace(" ", "-")
    tag = Tag(**payload)
    TagRepository(conn(repo_path)).save(tag)
    return tag.model_dump()


def create_dataset(repo_path: str, data: dict) -> dict:
    payload = dict(data)
    payload.pop("repo_path", None)
    dataset = EvalDataset(**payload)
    EvalDatasetRepository(conn(repo_path)).save(dataset)
    return dataset.model_dump()


def create_rubric(repo_path: str, data: dict) -> dict:
    payload = dict(data)
    payload.pop("repo_path", None)
    for item in payload.get("items", []):
        if item.get("description") and not item.get("prompt"):
            item["prompt"] = item["description"]
    rubric = Rubric(**payload)
    RubricRepository(conn(repo_path)).save(rubric)
    return _rubric_to_api(rubric)


def create_extractor(repo_path: str, data: dict) -> dict:
    payload = dict(data)
    payload.pop("repo_path", None)

    extractor_id = payload.get("id")
    python_code = payload.pop("python_code", None) or "def extract(trace):\n    return True"
    source_path = extractor_module.save_extractor_source(repo_path, extractor_id, python_code)

    payload["source_path"] = source_path
    payload["fingerprint"] = extractor_module.fingerprint_source(python_code)
    extractor = Extractor(**payload)
    ExtractorRepository(conn(repo_path)).save(extractor)

    dumped = extractor.model_dump()
    dumped["python_code"] = python_code
    return dumped


def create_gym(repo_path: str, data: dict) -> dict:
    payload = dict(data)
    payload.pop("repo_path", None)
    if not payload.get("id"):
        slug = payload.get("name", "").strip().lower().replace(" ", "-")
        payload["id"] = "".join(ch for ch in slug if ch.isalnum() or ch in "-_")
    if not payload.get("id"):
        raise ServiceError("Gym requires a name", 400)
    if not payload.get("class_path", "").strip():
        raise ServiceError("Gym requires a class_path", 400)
    gym = Gym(**payload)
    GymRepository(conn(repo_path)).save(gym)
    return gym.model_dump()


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


def generate_extractor_code(description: str) -> dict:
    try:
        code = extractor_module.generate_extractor_code(description)
        return {"code": code}
    except Exception as exc:
        raise ServiceError(str(exc), 500) from exc
