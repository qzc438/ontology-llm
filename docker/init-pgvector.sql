-- Run once, when the database directory is first created.
--
-- om_csv_to_database.py issues CREATE EXTENSION IF NOT EXISTS vector itself
-- before it needs the type, so a run would work without this. Doing it here as
-- well means a freshly created database reports healthy straight away, rather
-- than showing a failed check until somebody has started a matching task.
CREATE EXTENSION IF NOT EXISTS vector;
