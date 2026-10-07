#!/usr/bin/env python3
"""
Generates db/schema.sql (PostgreSQL DDL) from the SQLAlchemy models in backend/models.py,
so the SQL file can never drift from the code.

    python db/generate_schema.py            # (re)write db/schema.sql
    python db/generate_schema.py --check    # exit 1 if schema.sql is out of date (use in CI)

The output is idempotent: it can be run against an existing database without errors or data loss.
"""
import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

from sqlalchemy.dialects import postgresql  # noqa: E402
from sqlalchemy.schema import AddConstraint, CreateIndex, CreateTable, sort_tables_and_constraints  # noqa: E402

import models  # noqa: E402  (importing models does not need a database connection)

DIALECT = postgresql.dialect()

HEADER = """\
-- =====================================================================================================
-- Car Rental Management System - PostgreSQL schema
-- GENERATED FILE - do not edit by hand. Edit backend/models.py and run:  python db/generate_schema.py
-- Safe to run repeatedly (everything is IF NOT EXISTS / guarded).
-- =====================================================================================================

"""

UPDATED_AT_TRIGGER = """\
-- ----- updated_at maintenance (MySQL had ON UPDATE CURRENT_TIMESTAMP; Postgres needs a trigger) ---------
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_customer_updated_at ON customer;
CREATE TRIGGER trg_customer_updated_at BEFORE UPDATE ON customer
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
"""


def ddl(element) -> str:
    return str(element.compile(dialect=DIALECT)).strip()


def build() -> str:
    parts = [HEADER, "-- ----- tables " + "-" * 80 + "\n"]
    deferred = []
    for table, fkcs in sort_tables_and_constraints(models.Base.metadata.sorted_tables):
        if table is None:
            deferred = list(fkcs)
            continue
        parts.append(ddl(CreateTable(table, include_foreign_key_constraints=fkcs, if_not_exists=True)) + ";\n")

    # employee <-> location reference each other, so those foreign keys are added afterwards (guarded)
    parts.append("-- ----- circular foreign keys (employee <-> location) " + "-" * 40 + "\n")
    for fkc in deferred:
        if fkc.name is None:  # same name Postgres would pick on its own
            fkc.name = f"{fkc.parent.name}_{fkc.column_keys[0]}_fkey"
    deferred.sort(key=lambda c: c.name)  # sort_tables_and_constraints returns a set -> keep the output deterministic
    for fkc in deferred:
        parts.append(
            "DO $$ BEGIN\n"
            f"    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{fkc.name}'\n"
            f"                   AND conrelid = '{fkc.parent.name}'::regclass) THEN\n"
            f"        {ddl(AddConstraint(fkc))};\n"
            "    END IF;\n"
            "END $$;\n"
        )

    parts.append("-- ----- indexes " + "-" * 79 + "\n")
    for table in models.Base.metadata.sorted_tables:
        for idx in sorted(table.indexes, key=lambda i: i.name):
            parts.append(ddl(CreateIndex(idx, if_not_exists=True)) + ";\n")

    parts.append(UPDATED_AT_TRIGGER)
    return "\n".join(parts)


if __name__ == "__main__":
    sql = build()
    if "--check" in sys.argv:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if current != sql:
            print("db/schema.sql is OUT OF DATE - run: python db/generate_schema.py")
            sys.exit(1)
        print("db/schema.sql is up to date")
    else:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(sql)
        print(f"wrote {OUT}")
