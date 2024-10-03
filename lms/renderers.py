from datetime import UTC, datetime

from pyramid.renderers import JSON


def json_iso_utc():
    """Return a JSON renderer that formats dates as `isoformat`.

    This renderer assumes datetimes without tz info are in UTC and
    includes that in the datetime objects so the resulting string
    includes tz information.
    """

    renderer = JSON()

    def _datetime_adapter(obj: datetime, _request) -> str:
        if not obj.tzinfo:
            obj = obj.replace(tzinfo=UTC)
        return obj.isoformat()

    renderer.add_adapter(datetime, _datetime_adapter)

    return renderer
