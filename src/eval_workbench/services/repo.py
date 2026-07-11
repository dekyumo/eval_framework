import os
import shutil

from src.eval_workbench.repo_layout import eval_framework_root

DB_WIPE_ENV_VAR = "YES_I_WANT_TO_BE_ABLE_TO_WIPE_THE_WHOLE_DB_IN_EVAL_FRAMEWORK_FOR_TEST_PURPOSES"


def db_wipe_allowed() -> bool:
    return os.environ.get(DB_WIPE_ENV_VAR) == "1"
from src.eval_workbench.storage.kuzu_store import close_all, get_connection
from src.eval_workbench.storage.schema import init_schema


def get_repo_path(repo_path: str) -> dict:
    return {"repo_path": repo_path}


def reset_database(repo_path: str) -> dict:
    close_all()

    root = eval_framework_root(repo_path)
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)

    try:
        connection = get_connection(repo_path)
        init_schema(connection)
    except Exception as exc:
        print("Error resetting schema in Kuzu DB:", exc)

    return {"status": "reset_success"}
