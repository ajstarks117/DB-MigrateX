import os
from click.testing import CliRunner
from migrmgr import parser
from migrmgr.cli import cli


def test_cli_dry_run_outputs_plan_and_checksum():
    base = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'examples', 'migrations'))
    runner = CliRunner()
    result = runner.invoke(cli, ['migrate', '--migrations-dir', base, '--dry-run'])
    assert result.exit_code == 0
    out = result.output
   
    assert 'Planned migrations:' in out
    assert '001_create_users.sql' in out or '001' in out

    sql_path = os.path.join(base, '001_create_users.sql')
    chk = parser.checksum(sql_path)
    assert chk in out
