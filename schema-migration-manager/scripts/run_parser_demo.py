from migrmgr import parser
import os

base = os.path.join(os.path.dirname(__file__), '..', 'examples', 'migrations')
sql_path = os.path.normpath(os.path.join(base, '001_create_users.sql'))

mig = parser.parse_migration(sql_path)
print('id:', mig.id)
print('filename:', mig.filename)
print('author:', mig.author)
print('description:', mig.description)
print('requires:', mig.requires)
print('checksum:', mig.checksum)
