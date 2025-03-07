from datetime import UTC, datetime

import pytest

from lms.models.family import Family
from tests import factories


def test_lms_course_application_instance(db_session):
    old_ai = factories.ApplicationInstance()
    new_ai = factories.ApplicationInstance()

    lms_course = factories.LMSCourse()
    factories.LMSCourseApplicationInstance(
        lms_course=lms_course,
        application_instance=old_ai,
        updated=datetime(2021, 1, 1, tzinfo=UTC),
    )
    factories.LMSCourseApplicationInstance(
        lms_course=lms_course,
        application_instance=new_ai,
        updated=datetime(2025, 1, 1, tzinfo=UTC),
    )
    db_session.flush()

    assert lms_course.application_instances == [new_ai, old_ai]


@pytest.mark.parametrize("family", Family)
@pytest.mark.parametrize("lms_api_course_id", [None, "COURSE_ID"])
@pytest.mark.parametrize(
    "lms_url", ["", "https://example.com", "https://example.com//"]
)
def test_lms_url(family, db_session, lms_api_course_id, lms_url):
    ai = factories.ApplicationInstance(
        tool_consumer_info_product_family_code=family, lms_url=lms_url
    )
    lms_course = factories.LMSCourse(lms_api_course_id=lms_api_course_id)

    factories.LMSCourseApplicationInstance(
        application_instance=ai, lms_course=lms_course
    )
    db_session.flush()

    if family != Family.CANVAS or not lms_api_course_id or not lms_url:
        assert lms_course.lms_url is None
    else:
        assert lms_course.lms_url == "https://example.com/courses/COURSE_ID"
