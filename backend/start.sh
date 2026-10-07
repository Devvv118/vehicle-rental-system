#!/usr/bin/env bash
# Render start command:  bash start.sh
#   RESET_DB_ON_START=1  -> wipe the database and reload the demo data on every start (portfolio demo)
#   anything else        -> just make sure the schema exists (idempotent, keeps data)
set -e
if [ "$RESET_DB_ON_START" = "1" ]; then
    python db/init_db.py --reset --yes --sample-data
else
    python db/init_db.py
fi
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
