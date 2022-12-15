DROP VIEW IF EXISTS report.group_bubbled_activity CASCADE;

-- A weekly count of groups with annotation activity, but with counts summed
-- up and down between parents and children as appropriate.

-- For the moment this is a shim which is just proxying the non-bubbled counts
-- for now.
CREATE VIEW report.group_bubbled_activity AS (
    SELECT * FROM report.group_activity
);
