import asyncio

from src.eval_workbench.run_coro_sync import run_coro_sync


async def _answer() -> str:
    return "ok"


def test_run_coro_sync_from_running_loop():
    async def outer() -> str:
        return run_coro_sync(_answer())

    assert asyncio.run(outer()) == "ok"


def test_run_coro_sync_without_running_loop():
    assert run_coro_sync(_answer()) == "ok"
