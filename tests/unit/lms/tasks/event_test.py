from contextlib import contextmanager

import pytest

from lms.tasks.event import insert_event


def test_insert_event(event_service, BaseEvent):
    insert_event({"type": "value"})

    BaseEvent.assert_called_once_with(type="value")
    event_service.insert_event.assert_called_once_with(BaseEvent.return_value)


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
