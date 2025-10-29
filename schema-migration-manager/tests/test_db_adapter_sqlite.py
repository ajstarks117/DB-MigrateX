import os
import tempfile
from migrmgr.db import SqliteAdapter


def test_sqlite_adapter_basic(tmp_path):
    db_file = tmp_path / 'test.db'
    adapter = SqliteAdapter(str(db_file))
    adapter.connect()

    # create table
    adapter.execute('CREATE TABLE schema_versions (version TEXT PRIMARY KEY, description TEXT)')

    # insert and read
    adapter.execute('INSERT INTO schema_versions (version, description) VALUES (?, ?)', ('001', 'create users'))
    row = adapter.fetchone('SELECT version, description FROM schema_versions WHERE version = ?', ('001',))

    assert row is not None
    assert row['version'] == '001'
    assert row['description'] == 'create users'

    adapter.close()
