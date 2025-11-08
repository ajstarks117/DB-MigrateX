import os
import time
from pathlib import Path

import pytest

from app import app
from migrmgr.state import DatabaseState


MIGRATIONS_DIR = Path("migrations")


def ensure_migrations_dir():
    MIGRATIONS_DIR.mkdir(exist_ok=True)


def write_down_file(name, sql="-- down\nDROP TABLE IF EXISTS tmp_test;\n"):
    ensure_migrations_dir()
    p = MIGRATIONS_DIR / name
    p.write_text(sql, encoding="utf8")
    return p


def clear_record(state: DatabaseState, migration_id: str):
    try:
        state.cursor.execute("DELETE FROM schema_versions WHERE migration_id = ?", (migration_id,))
        state.conn.commit()
    except Exception:
        pass


def insert_applied(state: DatabaseState, migration_id: str, down_filename: str, applied_at: str = None):
    # insert a record into schema_versions
    # check table columns to be tolerant of older schema using 'version' column
    state.cursor.execute("PRAGMA table_info(schema_versions)")
    cols = [r[1] for r in state.cursor.fetchall()]
    id_col = 'migration_id' if 'migration_id' in cols else ('version' if 'version' in cols else 'migration_id')

    # build insert based on available columns so tests work on older schemas
    available = set(cols)
    fields = [id_col]
    values = [migration_id]

    if 'filename' in available:
        fields.append('filename'); values.append(f"{migration_id}.sql")
    if 'checksum' in available:
        fields.append('checksum'); values.append('chk')
    if 'applied_by' in available:
        fields.append('applied_by'); values.append('test')
    if 'down_filename' in available:
        fields.append('down_filename'); values.append(down_filename)
    if applied_at and 'applied_at' in available:
        fields.append('applied_at'); values.append(applied_at)

    placeholders = ','.join(['?'] * len(values))
    sql = f"INSERT OR REPLACE INTO schema_versions ({', '.join(fields)}) VALUES ({placeholders})"
    state.cursor.execute(sql, tuple(values))
    state.conn.commit()


@pytest.fixture(autouse=True)
def client_and_state(tmp_path, monkeypatch):
    # run tests with the project cwd so DatabaseState uses dev.sqlite3 in repo root
    root = Path.cwd()
    # ensure a fresh DatabaseState uses the existing dev.sqlite3 (may be reused)
    state = DatabaseState(None)

    # provide Flask test client
    app.testing = True
    client = app.test_client()

    yield client, state

    # teardown: remove test migration records we may have left
    try:
        state.cursor.execute("DELETE FROM schema_versions WHERE applied_by = ?", ("test",))
        state.conn.commit()
    except Exception:
        pass
    state.close()


def test_rollback_single_endpoint_success(client_and_state):
    client, state = client_and_state

    mig = "ut_rollback_1"
    down_name = "ut_rollback_1_down.sql"
    write_down_file(down_name, sql="DROP TABLE IF EXISTS ut_tmp_1;")

    # ensure clean
    clear_record(state, mig)

    insert_applied(state, mig, down_name)

    resp = client.post(f"/rollback/{mig}")
    text = resp.get_data(as_text=True)
    assert resp.status_code == 200, text
    assert "Rolled back" in text or "✅" in text

    # migration should be gone
    applied = state.get_applied_migrations()
    assert mig not in applied


def test_rollback_to_endpoint_success(client_and_state):
    client, state = client_and_state

    # create three applied migrations m1 < m2 < m3 (applied_at sequential)
    m1, m2, m3 = "ut_m1", "ut_m2", "ut_m3"
    d1, d2, d3 = "ut_m1_down.sql", "ut_m2_down.sql", "ut_m3_down.sql"

    write_down_file(d1)
    write_down_file(d2)
    write_down_file(d3)

    # clean any previous
    for m in (m1, m2, m3):
        clear_record(state, m)

    # insert with slight time offsets so applied_at ordering is preserved
    t = int(time.time())
    insert_applied(state, m1, d1, applied_at=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)))
    insert_applied(state, m2, d2, applied_at=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t + 1)))
    insert_applied(state, m3, d3, applied_at=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t + 2)))

    resp = client.post(f"/rollback_to/{m1}")
    text = resp.get_data(as_text=True)
    assert resp.status_code == 200, text
    assert "Rolled back" in text or "✅" in text

    applied = state.get_applied_migrations()
    # only m1 should remain
    assert applied == [m1] or (len(applied) == 1 and applied[0] == m1)
