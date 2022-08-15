from unittest.mock import sentinel

from lms.events.event import BaseEvent
from lms.events.subscribers import handle_event


def test_handle_event(event_service, pyramid_request):
    event = BaseEvent(request=pyramid_request, type=sentinel.type)

    handle_event(event)

    event_service.insert_event.assert_called_once_with(event)
