from datetime import UTC, datetime
from unittest.mock import sentinel
from zoneinfo import ZoneInfo

import pytest

from lms.renderers import json_iso_utc


@pytest.mark.parametrize(
    "time,expected",
    [
        # No timezone, UTC is assumed
        (datetime(2024, 1, 1), "2024-01-01T00:00:00+00:00"),
        # UTC, UTC is left intact
        (datetime(2024, 1, 1, tzinfo=UTC), "2024-01-01T00:00:00+00:00"),
        # Non-UTC, timezone is also left intact
        (
            datetime(2024, 1, 1, tzinfo=ZoneInfo("Europe/Madrid")),
            "2024-01-01T00:00:00+01:00",
        ),
    ],
)
def test_json_iso_utc(time, expected):
    assert (
        json_iso_utc()(sentinel.info)({"time": time}, {})
        == f"""{{"time": "{expected}"}}"""
    )
