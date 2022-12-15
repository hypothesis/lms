DROP VIEW IF EXISTS report.group_bubbled_counts CASCADE;

-- Counts for groups which do not depend on time, one row per group, but with
-- counts summed up and down between parents and children as appropriate.

-- For the moment this is a shim which is just proxying the non-bubbled counts
-- for now.
CREATE VIEW report.group_bubbled_counts AS (
    SELECT * FROM report.group_counts
);
