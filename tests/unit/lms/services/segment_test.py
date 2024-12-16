from unittest.mock import sentinel

import pytest

from lms.services.segment import SegmentService, factory
from tests import factories


class TestSegmentService:
    def test_upsert_segments_with_group_set(self, svc, group_set_service, db_session):
        course = factories.LMSCourse(course=factories.Course())
        groups = factories.CanvasGroup.create_batch(5, parent=course.course)
        group_set = factories.LMSGroupSet(lms_course=course)
        group_set_service.find_group_set.return_value = group_set
        db_session.flush()

        segments = svc.upsert_segments(course, groups[0].type, groups, group_set.lms_id)

        group_set_service.find_group_set.assert_called_once_with(
            course.course.application_instance,
            lms_id=group_set.lms_id,
            context_id=course.lti_context_id,
        )
        assert {
            (s.type, s.lms_course.h_authority_provided_id, s.name, s.lms_id)
            for s in segments
        } == {
            (g.type, g.parent.authority_provided_id, g.name, g.lms_id) for g in groups
        }

    def test_upsert_segments(self, svc, db_session):
        course = factories.LMSCourse(course=factories.Course())
        groups = factories.CanvasGroup.create_batch(5, parent=course.course)
        db_session.flush()

        segments = svc.upsert_segments(course, groups[0].type, groups)

        assert {
            (s.type, s.lms_course.h_authority_provided_id, s.name, s.lms_id)
            for s in segments
        } == {
            (g.type, g.parent.authority_provided_id, g.name, g.lms_id) for g in groups
        }

    @pytest.mark.parametrize("with_flush", [True, False])
    def test_upsert_segment_memberships(self, svc, db_session, with_flush):
        segments = factories.LMSSegment.create_batch(5)
        lms_user = factories.LMSUser()
        roles = factories.LTIRole.create_batch(3)

        if with_flush:
            db_session.flush()

        svc.upsert_segment_memberships(
            lms_user=lms_user, segments=segments, lti_roles=roles
        )

    def test_get_segment(self, svc, db_session):
        segment = factories.LMSSegment()
        db_session.flush()

        assert svc.get_segment(segment.h_authority_provided_id) == segment

    @pytest.fixture
    def svc(self, db_session, group_set_service):
        return SegmentService(db=db_session, group_set_service=group_set_service)


class TestFactory:
    def test_it(self, pyramid_request, SegmentService, db_session, group_set_service):
        service = factory(sentinel.context, pyramid_request)

        SegmentService.assert_called_once_with(
            db=db_session, group_set_service=group_set_service
        )
        assert service == SegmentService.return_value

    @pytest.fixture
    def SegmentService(self, patch):
        return patch("lms.services.segment.SegmentService")
