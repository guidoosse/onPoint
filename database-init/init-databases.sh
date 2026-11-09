#!/bin/sh
set -eu

psql --set ON_ERROR_STOP=1 <<'SQL'
SELECT 'CREATE DATABASE outline'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'outline')
\gexec

SELECT 'CREATE DATABASE vikunja'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'vikunja')
\gexec
SQL