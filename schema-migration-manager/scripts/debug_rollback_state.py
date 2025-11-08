from migrmgr.state import DatabaseState
from migrmgr.executor import MigrationExecutor
import os

print('CWD:', os.getcwd())
state = DatabaseState(None)
print('DB mode:', state._mode)
# clear any existing
try:
    state.cursor.execute("DELETE FROM schema_versions WHERE migration_id = ?", ('ut_rollback_1',))
    state.conn.commit()
except Exception as e:
    print('clear error', e)

# insert applied similar to test helper
state.cursor.execute("PRAGMA table_info(schema_versions)")
cols = [r[1] for r in state.cursor.fetchall()]
print('cols:', cols)

# follow test helper behavior: choose id_col based on existing columns
id_col = 'migration_id' if 'migration_id' in cols else ('version' if 'version' in cols else 'migration_id')
available = set(cols)
fields = [id_col]
values = ['ut_rollback_1']

if 'filename' in available:
    fields.append('filename'); values.append('ut_rollback_1.sql')
if 'checksum' in available:
    fields.append('checksum'); values.append('chk')
if 'applied_by' in available:
    fields.append('applied_by'); values.append('test')
if 'down_filename' in available:
    fields.append('down_filename'); values.append('ut_rollback_1_down.sql')

placeholders = ','.join(['?']*len(values))
sql = f"INSERT OR REPLACE INTO schema_versions ({', '.join(fields)}) VALUES ({placeholders})"
print('inserting SQL:', sql, 'values:', values)
state.cursor.execute(sql, tuple(values))
state.conn.commit()

# now create executor and check
exec = MigrationExecutor(None)
print('Executor adapter path:', getattr(exec.adapter, 'path', None))
rec = exec.adapter.get_applied('ut_rollback_1')
print('rec from adapter.get_applied():', rec)

state.close()
exec.close()
print('done')
