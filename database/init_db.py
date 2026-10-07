#!/usr/bin/env python3
"""
Initialise the PostgreSQL database for the Car Rental Management System.

    python database/init_db.py                  # create tables + reference data (idempotent, safe to re-run)
    python database/init_db.py --create-db      # ...and CREATE DATABASE first if it does not exist yet
    python database/init_db.py --sample-data    # ...and load a few demo locations/vehicles/customers
    python database/init_db.py --reset --yes    # DROP EVERYTHING in the database, then rebuild (destructive!)

The connection comes from the DATABASE_URL environment variable, or from backend/.env, e.g.
    DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/car_rental

Steps:  schema.sql (tables, indexes, triggers)  ->  seed.sql (membership tiers, insurance plans, features)
        ->  sample_data.sql (only with --sample-data)
"""
import argparse
import os
import sys

import psycopg2
from psycopg2 import sql as pgsql
from sqlalchemy.engine import make_url

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        try:
            from dotenv import load_dotenv
            load_dotenv(os.path.join(ROOT, "backend", ".env"))
            url = os.getenv("DATABASE_URL")
        except ImportError:
            pass
    if not url:
        sys.exit("DATABASE_URL is not set (environment or backend/.env). Example:\n"
                 "  DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/car_rental")
    return url


def connect(url, dbname=None, autocommit=False):
    kwargs = dict(host=url.host or "localhost", port=url.port or 5432, user=url.username,
                  password=url.password, dbname=dbname or url.database)
    kwargs.update({k: v for k, v in (url.query or {}).items() if k in ("sslmode", "connect_timeout")})
    conn = psycopg2.connect(**kwargs)
    conn.autocommit = autocommit
    return conn


def run_file(conn, filename):
    with open(os.path.join(HERE, filename), encoding="utf-8") as f, conn.cursor() as cur:
        cur.execute(f.read())
    print(f"  applied {filename}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--create-db", action="store_true", help="create the database if it does not exist")
    ap.add_argument("--reset", action="store_true", help="DROP all tables/data in the database first (needs --yes)")
    ap.add_argument("--yes", action="store_true", help="confirm destructive --reset")
    ap.add_argument("--sample-data", action="store_true", help="also load demo data (only into an empty database)")
    ap.add_argument("--no-seed", action="store_true", help="skip seed.sql (membership tiers etc.)")
    args = ap.parse_args()

    url = make_url(load_database_url())
    if not url.drivername.startswith("postgres"):
        sys.exit(f"DATABASE_URL must be a PostgreSQL URL, got driver '{url.drivername}'")
    db = url.database
    print(f"Target: {url.host or 'localhost'}:{url.port or 5432}/{db} (user {url.username})")

    if args.reset and not args.yes:
        sys.exit("--reset deletes ALL data in this database. Re-run with --reset --yes to confirm.")

    # 1. create the database if requested / needed
    if args.create_db:
        admin = connect(url, dbname="postgres", autocommit=True)
        with admin.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db,))
            if cur.fetchone():
                print(f"  database '{db}' already exists")
            else:
                cur.execute(pgsql.SQL("CREATE DATABASE {}").format(pgsql.Identifier(db)))
                print(f"  created database '{db}'")
        admin.close()

    try:
        conn = connect(url)
    except psycopg2.OperationalError as e:
        sys.exit(f"Could not connect: {str(e).strip()}\n"
                 f"Hint: create the database first (CREATE DATABASE {db};) or pass --create-db.")

    try:
        with conn:
            if args.reset:
                with conn.cursor() as cur:
                    cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
                print("  dropped and recreated schema 'public'")
            run_file(conn, "schema.sql")
            if not args.no_seed:
                run_file(conn, "seed.sql")
            if args.sample_data:
                run_file(conn, "sample_data.sql")
        # report
        with conn.cursor() as cur:
            cur.execute("SELECT relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                        "WHERE n.nspname = 'public' AND c.relkind = 'r' ORDER BY relname")
            tables = [r[0] for r in cur.fetchall()]
            print(f"\nDatabase ready: {len(tables)} tables")
            for t in tables:
                cur.execute(pgsql.SQL("SELECT COUNT(*) FROM {}").format(pgsql.Identifier(t)))
                print(f"  {t:<30} {cur.fetchone()[0]:>5} rows")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
