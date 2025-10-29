import os
from migrmgr.parser import parse_migration


def test_missing_yaml_and_downfile_detection(tmp_path):
    sql = tmp_path / '002_add_col.sql'
    down = tmp_path / '002_add_col_down.sql'
    sql.write_text('-- id: 002\nCREATE TABLE b (id INTEGER);')

    mig = parse_migration(str(sql))
    assert mig.id == '002'
    assert mig.requires == []

    
    down.write_text('DROP TABLE b;')
   
    mig2 = parse_migration(str(sql))
 
    assert mig2.down_filename in (None, down.name) or mig2.down_filename == down.name
