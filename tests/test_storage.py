from src.eval_workbench.storage.kuzu_store import get_connection, close_all
import pytest
from src.eval_workbench.storage.repositories import TagRepository
from src.eval_workbench.domain.tag import Tag


def test_kuzu_connection(tmp_path):
    repo_path = str(tmp_path / "agent_repo")
    repo_path_dir = tmp_path / "agent_repo"
    repo_path_dir.mkdir()

    try:
        conn = get_connection(repo_path)
        assert conn is not None

        repo = TagRepository(conn)
        tag = Tag(id="test_tag", name="test_tag", color="#ff0000", description="A test tag")
        repo.save(tag)

        loaded = repo.get("test_tag")
        assert loaded is not None
        assert loaded.name == "test_tag"
        assert loaded.color == "#ff0000"
        assert loaded.description == "A test tag"

        eval_framework_dir = repo_path_dir / "eval_framework"
        assert eval_framework_dir.exists()
        assert (eval_framework_dir / "eval.kuzu").exists()

    finally:
        close_all()
