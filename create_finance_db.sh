#!/bin/bash
set -e

# Create finance_db and initialize with schema+data
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE finance_db OWNER uac_user;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "finance_db" -f /init_finance_db.sql
