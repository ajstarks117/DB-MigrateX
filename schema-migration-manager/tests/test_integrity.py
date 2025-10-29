import os
from pathlib import Path

import pytest

from migrmgr import parser
from migrmgr.executor import MigrationExecutor


def test_precheck_detects_nulls(tmp_path, monkeypatch):
    migrations_dir = tmp_path / 'migrations'
    migrations_dir.mkdir()

    # create a users table with a NULL email
    db_file = tmp_path / 'int.db'
    # create DB and table
    exec_init = MigrationExecutor(db_path=str(db_file))
    exec_init.adapter.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)')
    exec_init.adapter.execute('INSERT INTO users (email) VALUES (NULL)')
    exec_init.commit = exec_init.adapter.commit
    exec_init.close()

    # migration that attempts to set email NOT NULL
    up = migrations_dir / '001_set_not_null.sql'
    up.write_text('ALTER TABLE users ALTER COLUMN email SET NOT NULL;', encoding='utf8')

    migrations = parser.parse_migrations(str(migrations_dir))
    m = migrations[0]

    monkeypatch.chdir(tmp_path)
    exec_ = MigrationExecutor(db_path=str(db_file))

    with pytest.raises(Exception):
        exec_.apply_migration(m, user='tester')

    exec_.close()


def test_safe_column_addition_succeeds(tmp_path, monkeypatch):
    migrations_dir = tmp_path / 'migrations'
    migrations_dir.mkdir()

    db_file = tmp_path / 'int2.db'
    exec_init = MigrationExecutor(db_path=str(db_file))
    exec_init.adapter.execute('CREATE TABLE t (id INTEGER PRIMARY KEY)')
    exec_init.close()

    up = migrations_dir / '001_add_col.sql'
    down = migrations_dir / '001_add_col_down.sql'
    # migration that doesn't set NOT NULL
    up.write_text('ALTER TABLE t ADD COLUMN newcol INTEGER;', encoding='utf8')
    down.write_text('-- down', encoding='utf8')

    migrations = parser.parse_migrations(str(migrations_dir))
    m = migrations[0]

    monkeypatch.chdir(tmp_path)
    exec_ = MigrationExecutor(db_path=str(db_file))
    exec_.apply_migration(m, user='tester')

    exec_.close()
