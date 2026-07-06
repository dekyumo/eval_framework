import kuzu

from src.eval_workbench.storage.kuzu_store import get_connection


def conn(repo_path: str) -> kuzu.Connection:
    return get_connection(repo_path)
