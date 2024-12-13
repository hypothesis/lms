from contextlib import contextmanager
from datetime import datetime

import pytest
from freezegun import freeze_time

from lms.tasks.event import insert_event, purge_launch_data
from tests import factories


def test_insert_event(event_service, BaseEvent, pyramid_request):
    insert_event({"type": "value"})

    BaseEvent.assert_called_once_with(request=pyramid_request, type="value")
    event_service.insert_event.assert_called_once_with(BaseEvent.return_value)


@freeze_time("2024-1-25")
def test_purge_launch_data():
    recent_data = factories.EventData(
        event=factories.Event(timestamp=datetime(2024, 1, 20)),
        data={"lti_params": {"some": "data"}},
    )
    old_data = factories.EventData(
        event=factories.Event(timestamp=datetime(2024, 1, 10)),
        data={"lti_params": {"some": "data"}},
    )
    old_data_no_launch = factories.EventData(
        event=factories.Event(timestamp=datetime(2024, 1, 10)),
        data={"some_other_data": {"some": "data"}},
    )

    purge_launch_data(max_age_days=10)

    # Kept data for recent launches
    assert "lti_params" in recent_data.data
    # Removed for events in the time window
    assert "lti_params" not in old_data.data
    # Other keys are not removed
    assert "some_other_data" in old_data_no_launch.data


@pytest.fixture(autouse=True)
def BaseEvent(patch):
    return patch("lms.tasks.event.BaseEvent")


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.event.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
