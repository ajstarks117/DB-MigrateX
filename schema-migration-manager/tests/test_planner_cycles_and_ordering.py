from migrmgr.planner import MigrationPlanner, MigrationPlanError
from migrmgr.parser import Migration


def test_planner_detects_cycle():
    a = Migration(id='001', filename='001.sql', up_sql='--', down_filename=None, author=None, description=None, requires=['003'], checksum='x', type=None)
    b = Migration(id='002', filename='002.sql', up_sql='--', down_filename=None, author=None, description=None, requires=['001'], checksum='y', type=None)
    c = Migration(id='003', filename='003.sql', up_sql='--', down_filename=None, author=None, description=None, requires=['002'], checksum='z', type=None)

    planner = MigrationPlanner()
    try:
        planner.build_plan([a, b, c])
        assert False, "Expected MigrationPlanError due to cycle"
    except MigrationPlanError:
        pass


def test_planner_orders_dependencies():
    base = Migration(id='000', filename='000.sql', up_sql='--', down_filename=None, author=None, description=None, requires=[], checksum='a', type=None)
    one = Migration(id='001', filename='001.sql', up_sql='--', down_filename=None, author=None, description=None, requires=['000'], checksum='b', type=None)
    two = Migration(id='002', filename='002.sql', up_sql='--', down_filename=None, author=None, description=None, requires=['001'], checksum='c', type=None)

    planner = MigrationPlanner()
    plan = planner.build_plan([one, two, base])
    ids = [m.id for m in plan]
    assert ids == ['000', '001', '002']
