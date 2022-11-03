-- Calculate the ratio of increase (or decrease) between two numbers taking
-- care not to trip over divide by zero issues.
-- For example:
--    Moving from 100 to 200 will give a ratio of +1.0
--    Moving from 200 to 100 will give a ratio of -0.5

CREATE OR REPLACE FUNCTION report.growth_ratio(previous BIGINT, current BIGINT)
RETURNS FLOAT4
IMMUTABLE
AS $$
    SELECT CASE
       WHEN previous != 0 THEN
        ((current - previous) / previous::FLOAT)::FLOAT4
    END
$$
LANGUAGE SQL;
