import os
from migrmgr import parser


def test_parse_example_migration(tmp_path):
    # use the example files included in the repo
    base = os.path.join(os.path.dirname(__file__), '..', 'examples', 'migrations')
    sql_path = os.path.normpath(os.path.join(base, '001_create_users.sql'))
    yml_path = os.path.normpath(os.path.join(base, '001_create_users.yml'))

    # ensure files exist in repo
    assert os.path.exists(sql_path), f"SQL example missing: {sql_path}"
    assert os.path.exists(yml_path), f"YAML example missing: {yml_path}"

    mig = parser.parse_migration(sql_path)

    assert mig.id == '001'
    assert mig.filename == '001_create_users.sql'
    assert 'CREATE TABLE users' in mig.up_sql
    assert mig.author == 'Alice'
    assert mig.description == 'Create users table'
    # requires should include 000_init as per YAML
    assert '000_init' in mig.requires
    # checksum should be a 64-char hex
    assert isinstance(mig.checksum, str) and len(mig.checksum) == 64
