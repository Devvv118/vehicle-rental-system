"""
Helpers to (re)build the demo database. Used by:
  * db/init_db.py            (command line / Render start script)
  * POST /admin/reset-demo   (the "Reset demo data" button in the UI)

Takes a plain psycopg2 connection, so it has no dependency on the app's engine.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def run_sql_file(conn, filename):
    with open(os.path.join(HERE, filename), encoding="utf-8") as f, conn.cursor() as cur:
        cur.execute(f.read())


def reset_demo_data(conn, sample_data=True):
    """DROP everything in the public schema and rebuild it: schema + reference data (+ demo data).

    Runs inside the caller's transaction; the caller commits. Destructive!
    """
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    run_sql_file(conn, "schema.sql")
    run_sql_file(conn, "seed.sql")
    if sample_data:
        run_sql_file(conn, "sample_data.sql")
