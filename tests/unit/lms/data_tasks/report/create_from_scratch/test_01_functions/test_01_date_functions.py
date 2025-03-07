from datetime import date

import importlib_resources
import pytest
from data_tasks.sql_script import SQLScript
from sqlalchemy import text

TASK_ROOT = importlib_resources.files("lms.data_tasks")


class TestDateFunctions:
    # We hardcode the date to avoid flakiness
    NOW = date(2025, 3, 6)

    @pytest.mark.usefixtures("with_date_functions")
    @pytest.mark.parametrize(
        "timescale,value,expected",
        (
            ("all_time", f"'{NOW}'::date", date(1901, 1, 1)),
            ("academic_year", f"'{NOW}'::date", date(2024, 7, 1)),
            ("semester", f"'{NOW}'::date", date(2025, 1, 1)),
            ("week", f"'{NOW}'::date", date(2025, 3, 2)),  # Weeks start on Sunday
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
