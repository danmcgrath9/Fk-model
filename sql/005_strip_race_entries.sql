-- fk.races.raw held the whole Race Form payload, every runner with every past run, which
-- fk.entries already stores. 917 races took 249 MB and the database hit its disk limit.
-- Every reader of races.raw wants race-level facts (going, rail, lws, startTime), so the
-- runners come out. Guarded: a row without an entries key is left alone, so re-running is
-- a no-op. The space is returned to the disk by VACUUM FULL, run separately because it
-- cannot run inside a transaction (scripts/db_reclaim.py does both).

update fk.races set raw = raw - 'entries' where raw ? 'entries';
