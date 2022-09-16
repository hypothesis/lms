from unittest.mock import sentinel

import pytest

from lms.events import BaseEvent
from lms.models import Event, EventData, EventType, EventUser
from lms.services.event import EventService, factory
from tests import factories


class TestEventService:
    def test_insert_event(self, svc, db_session):
        user = factories.User()
        db_session.flush()

        svc.insert_event(
            BaseEvent(
                request=sentinel.request,
                type=EventType.Type.CONFIGURED_LAUNCH,
                user_id=user.id,
                data={"some": "data"},
            )
        )
        assert (
            db_session.query(Event).one().type.type == EventType.Type.CONFIGURED_LAUNCH
        )

        assert db_session.query(EventUser).one().user_id == user.id
        assert db_session.query(EventData).one().data == {"some": "data"}

    def test_insert_event_mulitple_roles(self, svc, db_session):
        user = factories.User()
        roles = factories.LTIRole.create_batch(5)
        db_session.flush()

        svc.insert_event(
            BaseEvent(
                request=sentinel.request,
                type=EventType.Type.CONFIGURED_LAUNCH,
                user_id=user.id,
                role_ids=[role.id for role in roles],
                data={"some": "data"},
            )
        )
        event_users = db_session.query(EventUser).all()
        assert len(event_users) == 5
        assert {role.id for role in roles} == {
            event_user.lti_role_id for event_user in event_users
        }

    def test_insert_event_no_user(self, svc, db_session):
        svc.insert_event(
            BaseEvent(request=sentinel.request, type=EventType.Type.CONFIGURED_LAUNCH)
        )
        assert not db_session.query(EventUser).one_or_none()

    def test_insert_event_no_data(self, svc, db_session):
        svc.insert_event(
            BaseEvent(request=sentinel.request, type=EventType.Type.CONFIGURED_LAUNCH)
        )
        assert not db_session.query(EventData).one_or_none()

    def test_insert_event_type(self, svc, db_session):
        type_query = db_session.query(EventType).filter_by(
            type=EventType.Type.CONFIGURED_LAUNCH
        )

        # Insert the event type for the first time
        svc.insert_event(
            BaseEvent(request=sentinel.request, type=EventType.Type.CONFIGURED_LAUNCH)
        )

        # It will create a new type
        event_type = type_query.one()
        # Clear the @lru_cache of the private method
        svc._get_type_pk.cache_clear()  # pylint:disable=protected-access
        # Insert the event type again
        svc.insert_event(
            BaseEvent(request=sentinel.request, type=EventType.Type.CONFIGURED_LAUNCH)
        )
        # The type is the same as the first insert
        assert event_type == type_query.one()

    @pytest.fixture
    def svc(self, db_session):
        return EventService(db_session)


class TestFactory:
    def test_it(self, pyramid_request, EventService):
        svc = factory(sentinel.context, pyramid_request)

        EventService.assert_called_once_with(db=pyramid_request.db)
        assert svc == EventService.return_value

    @pytest.fixture
    def EventService(self, patch):
        return patch("lms.services.event.EventService")
