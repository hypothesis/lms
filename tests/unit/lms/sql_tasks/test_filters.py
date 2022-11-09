import pytest

from lms.sql_tasks.filters import sql_literal


@pytest.mark.parametrize(
    "value,expected", [("string", "'string'"), ("with spaces", "'with spaces'")]
)
def test_sql_literal(value, expected):
    assert sql_literal(value) == expected
