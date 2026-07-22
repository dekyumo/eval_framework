import kuzu
import os
import threading
from contextlib import contextmanager

from src.eval_workbench.repo_layout import db_path as repo_db_path

_db_connections: dict[str, kuzu.Connection] = {}
_dbs: dict[str, kuzu.Database] = {}
_kuzu_lock = threading.RLock()


class _LockedConnection:
    """Serialize Kuzu access — embedded DB is not safe across threads on one connection."""

    def __init__(self, conn: kuzu.Connection):
        object.__setattr__(self, "_conn", conn)

    def execute(self, *args, **kwargs):
        with _kuzu_lock:
            return self._conn.execute(*args, **kwargs)

    def close(self):
        with _kuzu_lock:
            return self._conn.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)


def _get_db_path_for_repo(repo_path: str) -> str:
    return repo_db_path(repo_path)


def get_connection(repo_path: str) -> kuzu.Connection:
    if repo_path in _db_connections:
        return _LockedConnection(_db_connections[repo_path])  # type: ignore[return-value]

    db_file = _get_db_path_for_repo(repo_path)
    os.makedirs(os.path.dirname(db_file), exist_ok=True)

    with _kuzu_lock:
        db = kuzu.Database(db_file)
        conn = kuzu.Connection(db)

        from src.eval_workbench.storage.schema import init_schema
        init_schema(conn)

        _dbs[repo_path] = db
        _db_connections[repo_path] = conn

    return _LockedConnection(conn)  # type: ignore[return-value]


@contextmanager
def kuzu_transaction(connection: kuzu.Connection):
    with _kuzu_lock:
        connection.execute("BEGIN TRANSACTION")
        try:
            yield connection
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise


def close_all():
    with _kuzu_lock:
        for conn in _db_connections.values():
            conn.close()
        for db in _dbs.values():
            db.close()
        _db_connections.clear()
        _dbs.clear()
