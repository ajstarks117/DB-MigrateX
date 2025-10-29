from pathlib import Path
import pytest

from migrmgr import parser
from migrmgr.executor import MigrationExecutor, MigrationError


def test_apply_twice_skips(tmp_path, monkeypatch):
    migrations_dir = tmp_path / 'migrations'
    migrations_dir.mkdir()

    up = migrations_dir / '001_foo.sql'
    down = migrations_dir / '001_foo_down.sql'
    up.write_text('CREATE TABLE foo (id INTEGER PRIMARY KEY);', encoding='utf8')
    down.write_text('DROP TABLE foo;', encoding='utf8')

    migrations = parser.parse_migrations(str(migrations_dir))
    m = migrations[0]

    monkeypatch.chdir(tmp_path)
    exec_ = MigrationExecutor(db_path=str(tmp_path / 'id.db'))

    exec_.apply_migration(m, user='tester')
    # apply again should skip (no exception)
    exec_.apply_migration(m, user='tester')

    # now tamper the file to change checksum
    up.write_text('/* changed */\nCREATE TABLE foo (id INTEGER PRIMARY KEY);', encoding='utf8')
    new_m = parser.parse_migrations(str(migrations_dir))[0]

    with pytest.raises(Exception):
        exec_.apply_migration(new_m, user='tester')

    exec_.close()
