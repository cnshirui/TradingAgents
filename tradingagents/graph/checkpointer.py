"""LangGraph checkpoint support for resumable analysis runs.

Per-ticker SQLite databases so concurrent tickers don't contend.
"""

from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from tradingagents.dataflows.utils import safe_ticker_component

_CHECKPOINT_TIMEOUT_SECONDS = 60.0
_CHECKPOINT_BUSY_TIMEOUT_MS = int(_CHECKPOINT_TIMEOUT_SECONDS * 1000)


def _db_path(data_dir: str | Path, ticker: str) -> Path:
    """Return the SQLite checkpoint DB path for a ticker."""
    # Reject ticker values that would escape the checkpoints directory.
    safe = safe_ticker_component(ticker).upper()
    p = Path(data_dir) / "checkpoints"
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{safe}.db"


def _connect_checkpoint_db(db: Path) -> sqlite3.Connection:
    """Open a SQLite checkpoint connection tuned for LangGraph concurrency."""
    conn = sqlite3.connect(
        str(db),
        timeout=_CHECKPOINT_TIMEOUT_SECONDS,
        check_same_thread=False,
    )
    conn.execute(f"PRAGMA busy_timeout = {_CHECKPOINT_BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def thread_id(ticker: str, date: str) -> str:
    """Deterministic thread ID for a ticker+date pair."""
    return hashlib.sha256(f"{ticker.upper()}:{date}".encode()).hexdigest()[:16]


@contextmanager
def get_checkpointer(data_dir: str | Path, ticker: str) -> Generator[SqliteSaver, None, None]:
    """Context manager yielding a SqliteSaver backed by a per-ticker DB."""
    db = _db_path(data_dir, ticker)
    conn = _connect_checkpoint_db(db)
    try:
        saver = SqliteSaver(conn)
        saver.setup()
        yield saver
    finally:
        conn.close()


def has_checkpoint(data_dir: str | Path, ticker: str, date: str) -> bool:
    """Check whether a resumable checkpoint exists for ticker+date."""
    return checkpoint_step(data_dir, ticker, date) is not None


def checkpoint_step(data_dir: str | Path, ticker: str, date: str) -> int | None:
    """Return the step number of the latest checkpoint, or None if none exists."""
    db = _db_path(data_dir, ticker)
    if not db.exists():
        return None
    with get_checkpointer(data_dir, ticker) as saver:
        return checkpoint_step_from_saver(saver, ticker, date)


def checkpoint_step_from_saver(saver: SqliteSaver, ticker: str, date: str) -> int | None:
    """Return the latest checkpoint step using an already-open saver."""
    tid = thread_id(ticker, date)
    config = {"configurable": {"thread_id": tid}}
    cp = saver.get_tuple(config)
    if cp is None:
        return None
    return cp.metadata.get("step")


def clear_all_checkpoints(data_dir: str | Path) -> int:
    """Remove all checkpoint DBs. Returns number of files deleted."""
    cp_dir = Path(data_dir) / "checkpoints"
    if not cp_dir.exists():
        return 0
    dbs = list(cp_dir.glob("*.db"))
    for db in dbs:
        db.unlink()
        for suffix in ("-wal", "-shm"):
            sidecar = db.with_name(f"{db.name}{suffix}")
            if sidecar.exists():
                sidecar.unlink()
    return len(dbs)


def clear_checkpoint(data_dir: str | Path, ticker: str, date: str) -> None:
    """Remove checkpoint for a specific ticker+date by deleting the thread's rows."""
    db = _db_path(data_dir, ticker)
    if not db.exists():
        return
    tid = thread_id(ticker, date)
    conn = _connect_checkpoint_db(db)
    try:
        for table in ("writes", "checkpoints"):
            conn.execute(f"DELETE FROM {table} WHERE thread_id = ?", (tid,))
        conn.commit()
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()
