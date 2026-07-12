import kuzu
import os
from contextlib import contextmanager

from src.eval_workbench.repo_layout import db_path as repo_db_path

_db_connections: dict[str, kuzu.Connection] = {}
_dbs: dict[str, kuzu.Database] = {}


def _get_db_path_for_repo(repo_path: str) -> str:
    return repo_db_path(repo_path)


def get_connection(repo_path: str) -> kuzu.Connection:
    if repo_path in _db_connections:
        return _db_connections[repo_path]

    db_file = _get_db_path_for_repo(repo_path)
    os.makedirs(os.path.dirname(db_file), exist_ok=True)

    db = kuzu.Database(db_file)
    conn = kuzu.Connection(db)

    from src.eval_workbench.storage.schema import init_schema
    init_schema(conn)

    _dbs[repo_path] = db
    _db_connections[repo_path] = conn

    return conn


@contextmanager
def kuzu_transaction(connection: kuzu.Connection):
    connection.execute("BEGIN TRANSACTION")
    try:
        yield connection
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise


def close_all():
    for conn in _db_connections.values():
        conn.close()
    for db in _dbs.values():
        db.close()
    _db_connections.clear()
    _dbs.clear()
