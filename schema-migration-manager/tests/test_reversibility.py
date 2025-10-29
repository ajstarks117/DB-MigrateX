import os
from pathlib import Path

import pytest

from migrmgr import parser
from migrmgr.executor import MigrationExecutor, MigrationError


def test_apply_and_rollback(tmp_path, monkeypatch):
    migrations_dir = tmp_path / 'migrations'
    migrations_dir.mkdir()

    up = migrations_dir / '001_create_table.sql'
    down = migrations_dir / '001_create_table_down.sql'
    up.write_text('CREATE TABLE demo (id INTEGER PRIMARY KEY);', encoding='utf8')
    down.write_text('DROP TABLE demo;', encoding='utf8')

    migrations = parser.parse_migrations(str(migrations_dir))
    assert len(migrations) == 1

    # run with working dir set to tmp_path so executor finds migrations/<down_file>
    monkeypatch.chdir(tmp_path)
    db_file = tmp_path / 'test.db'
    exec_ = MigrationExecutor(db_path=str(db_file))

    m = migrations[0]
    exec_.apply_migration(m, user='tester')

    # table should exist
    r = exec_.adapter.fetchone("SELECT name FROM sqlite_master WHERE type='table' AND name='demo'")
    assert r is not None

    # rollback
    exec_.rollback_migration(m.id)
    r2 = exec_.adapter.fetchone("SELECT name FROM sqlite_master WHERE type='table' AND name='demo'")
    assert r2 is None

    exec_.close()


def test_missing_down_fails(tmp_path, monkeypatch):
    migrations_dir = tmp_path / 'migrations'
    migrations_dir.mkdir()

    up = migrations_dir / '002_nodown.sql'
    up.write_text('CREATE TABLE nodown (id INTEGER PRIMARY KEY);', encoding='utf8')

    migrations = parser.parse_migrations(str(migrations_dir))
    m = migrations[0]

    monkeypatch.chdir(tmp_path)
    exec_ = MigrationExecutor(db_path=str(tmp_path / 'test2.db'))

    with pytest.raises(Exception):
        exec_.apply_migration(m, user='tester')

    exec_.close()
