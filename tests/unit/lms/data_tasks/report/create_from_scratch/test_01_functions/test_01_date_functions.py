from datetime import UTC, datetime, timedelta

import importlib_resources
import pytest
from data_tasks.sql_script import SQLScript
from sqlalchemy import text

TASK_ROOT = importlib_resources.files("lms.data_tasks")


class TestDateFunctions:
    NOW = datetime(2025, 3, 6, tzinfo=UTC)  # We hardcode the date to avoid flakiness
    # 2024 was a leap year so the math accounts for that 366 days
    ONE_YEAR_AGO = (NOW - timedelta(days=366)).date()
    TWO_YEARS_AGO = (NOW - timedelta(days=366 + 365)).date()

    @pytest.mark.usefixtures("with_date_functions")
    @pytest.mark.parametrize(
        "timescale,value,expected",
        (
            ("trailing_year", "'2025/03/06'::date", ONE_YEAR_AGO),
            # Technically this test could fail if you run this exactly at midnight
            ("trailing_year", "'2025/03/06'::date - INTERVAL '1 second'", ONE_YEAR_AGO),
            ("trailing_year", "'2025/03/06'::date - INTERVAL '1 day'", ONE_YEAR_AGO),
            (
                "trailing_year",
                "'2025/03/06'::date - INTERVAL '1 year 1 day'",
                TWO_YEARS_AGO,
            ),
            (
                "trailing_year",
                "'2025/03/06'::date - INTERVAL '1 year 10 day'",
                TWO_YEARS_AGO,
            ),
        ),
    )
    def test_multi_truncate(self, db_session, timescale, value, expected):
        row = db_session.execute(
            text(f"SELECT report.multi_truncate('{timescale}', ({value})::DATE)")
        ).one_or_none()

        assert row[0] == expected

    @pytest.fixture
    def with_date_functions(self, db_session):
        db_session.execute(text("CREATE SCHEMA report"))

        script = SQLScript(
            path=str(
                TASK_ROOT
                / "report/create_from_scratch/01_functions/01_date_functions.sql"
            ),
            template_vars={},
        )
        # We need to iterate to trigger execution of the multiple queries in
        # this script
        tuple(script.execute(db_session))
