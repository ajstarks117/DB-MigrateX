import os
import tempfile
from migrmgr.parser import parse_migration, MigrationParseError


def test_malformed_yaml_raises(tmp_path):
    sql_file = tmp_path / '001_bad.sql'
    yml_file = tmp_path / '001_bad.yml'
    sql_file.write_text('-- id: 001\nCREATE TABLE a (id INTEGER);')
 
    yml_file.write_text('id: 001\nrequires: [unclosed_list')

    try:
        parse_migration(str(sql_file))
        assert False, "Expected MigrationParseError"
    except MigrationParseError:
        pass
