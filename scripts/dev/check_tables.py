import os
import sqlite3

# Resolve absolute path to backend/resume_rewriter.db relative to this script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(PROJECT_ROOT, 'backend', 'resume_rewriter.db')

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = c.fetchall()
print('Tables in database:', tables)
conn.close()
