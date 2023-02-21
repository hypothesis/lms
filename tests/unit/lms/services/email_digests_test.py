from datetime import datetime, timedelta
from unittest.mock import sentinel

import pytest

from lms.services.email_digests import EmailDigestsService
from tests import factories


class TestEmailDigestsService:
    def test_it_calls_the_h_api(self, svc, h_api, user, since, until):
        """It should make one call to the h API to get the activity."""
        activity = svc.get(user.id, since, until)

        h_api._api_request.assert_called_once_with(
            "GET",
            path="email_digests",
            params={
                "user": user.h_userid,
                "since": since.isoformat(),
                "until": until.isoformat(),
            },
        )

    def test_no_annotations(self, svc, h_api, user, since, until):
        """Test it when the h API reports no annotations."""
        activity = svc.get(user.id, since, until)

        assert activity == {"num_annotations": 0, "courses": []}

    def test_activity_from_a_course_group(self, svc, h_api, user, since, until):
        """Test when there's activity from a course group."""
        course = factories.Course()
        factories.GroupingMembership(
            grouping=course,
            user=user,
            lti_role=factories.LTIRole(value="Instructor"),
        )

        h_api._api_request.return_value["groups"] = [
            {
                "authority_provided_id": course.authority_provided_id,
                "users": [
                    {
                        "userid": factories.User().h_userid,
                        "num_annotations": 40,
                    },
                    {
                        "userid": factories.User().h_userid,
                        "num_annotations": 2,
                    },
                ],
            }
        ]

        activity = svc.get(user.id, since, until)

        assert activity == {
            "num_annotations": 42,
            "courses": [
                {
                    "title": course.lms_name,
                    "num_annotations": 42,
                },
            ],
        }

    def test_activity_from_a_non_course_group(self, svc, h_api, user, since, until):
        group = factories.CanvasGroup()
        factories.GroupingMembership(
            grouping=group.parent,
            user=user,
            lti_role=factories.LTIRole(value="Instructor"),
        )

        h_api._api_request.return_value["groups"] = [
            {
                "authority_provided_id": group.authority_provided_id,
                "users": [
                    {
                        "userid": factories.User().h_userid,
                        "num_annotations": 42,
                    },
                ],
            }
        ]

        activity = svc.get(user.id, since, until)

        assert activity == {
            "num_annotations": 42,
            "courses": [
                {
                    "title": group.parent.lms_name,
                    "num_annotations": 42,
                },
            ],
        }

    def test_activity_from_multiple_groups_in_the_same_course(
        self, svc, h_api, user, since, until
    ):
        course = factories.Course()
        groups = factories.CanvasGroup.create_batch(size=2, parent=course)
        factories.GroupingMembership(
            grouping=course,
            user=user,
            lti_role=factories.LTIRole(value="Instructor"),
        )

        h_api._api_request.return_value["groups"] = [
            dict(
                authority_provided_id=group.authority_provided_id,
                users=[
                    {
                        "userid": factories.User().h_userid,
                        "num_annotations": 21,
                    },
                ],
            )
            for group in groups
        ]

        activity = svc.get(user.id, since, until)

        assert activity == {
            "num_annotations": 42,
            "courses": [
                {
                    "title": course.lms_name,
                    "num_annotations": 42,
                },
            ],
        }

    def test_activity_from_a_course_group_with_multiple_groupings(
        self, svc, h_api, user, since, until
    ):
        # Course groupings with the same authority_provided_id but different
        # application instances.
        course_groupings = factories.Course.create_batch(
            size=2, authority_provided_id="TEST_AUTHORITY_PROVIDED_ID"
        )
        # Make the user an instructor in only one of the groupings.
        factories.GroupingMembership(
            grouping=course_groupings[1],
            user=user,
            lti_role=factories.LTIRole(value="Instructor"),
        )

        h_api._api_request.return_value["groups"] = [
            {
                "authority_provided_id": course_groupings[0].authority_provided_id,
                "users": [
                    {
                        "userid": factories.User().h_userid,
                        "num_annotations": 40,
                    },
                    {
                        "userid": factories.User().h_userid,
                        "num_annotations": 2,
                    },
                ],
            }
        ]

        activity = svc.get(user.id, since, until)

        assert activity == {
            "num_annotations": 42,
            "courses": [
                {
                    "title": course_groupings[0].lms_name,
                    "num_annotations": 42,
                },
            ],
        }

    def test_a_non_course_group_whose_course_has_multiple_groupings(
        self, svc, h_api, user, since, until
    ):
        courses = factories.Course.create_batch(
            size=2, authority_provided_id="TEST_AUTHORITY_PROVIDED_ID"
        )
        group = factories.CanvasGroup(parent=courses[0])
        factories.GroupingMembership(
            grouping=courses[1],
            user=user,
            lti_role=factories.LTIRole(value="Instructor"),
        )

        h_api._api_request.return_value["groups"] = [
            {
                "authority_provided_id": group.authority_provided_id,
                "users": [
                    {
                        "userid": factories.User().h_userid,
                        "num_annotations": 42,
                    },
                ],
            }
        ]

        activity = svc.get(user.id, since, until)

        assert activity == {
            "num_annotations": 42,
            "courses": [
                {
                    "title": courses[0].lms_name,
                    "num_annotations": 42,
                },
            ],
        }

    def test_activity_from_an_unrecognized_group(self, svc, h_api, user, since, until):
        """Test it when the h API returns a group with an unrecognized ID."""
        # The h API returns a group with an ID that doesn't exist in the LMS DB.
        h_api._api_request.return_value["groups"] = [
            {
                "authority_provided_id": "UNKNOWN_ID",
                "users": [
                    {
                        "userid": factories.User().h_userid,
                        "num_annotations": 42,
                    },
                ],
            },
        ]

        activity = svc.get(user.id, since, until)

        assert activity == {"num_annotations": 0, "courses": []}

    def test_activity_from_a_group_the_user_isnt_an_instructor_in(
        self, svc, h_api, user, since, until
    ):
        h_api._api_request.return_value["groups"] = [
            {
                "authority_provided_id": factories.Course().authority_provided_id,
                "users": [
                    {
                        "userid": factories.User().h_userid,
                        "num_annotations": 42,
                    },
                ],
            }
        ]

        activity = svc.get(user.id, since, until)

        assert activity == {"num_annotations": 0, "courses": []}

    def test_it_doesnt_count_the_users_own_annotations(
        self, svc, h_api, user, since, until
    ):
        course = factories.Course()
        factories.GroupingMembership(
            grouping=course,
            user=user,
            lti_role=factories.LTIRole(value="Instructor"),
        )

        h_api._api_request.return_value["groups"] = [
            {
                "authority_provided_id": course.authority_provided_id,
                "users": [
                    {
                        "userid": factories.User().h_userid,
                        "num_annotations": 40,
                    },
                    {
                        "userid": user.h_userid,
                        "num_annotations": 2,
                    },
                ],
            }
        ]

        activity = svc.get(user.id, since, until)

        assert activity == {
            "num_annotations": 40,
            "courses": [
                {
                    "title": course.lms_name,
                    "num_annotations": 40,
                },
            ],
        }

    def test_it_doesnt_count_non_course_instructors(self):
        # TODO: You need to filter LTIRoles by scope=course  otherwise you
        # might get people that are a teacher elsewhere in the institution. An
        # edge case but it does occur.
        # https://hypothes-is.slack.com/archives/C1MA4E9B9/p1676538418838019?thread_ts=1676484585.528569&cid=C1MA4E9B9
        pass

    def test_it_does_nothing_if_the_user_doesnt_exist(self, svc, h_api, since, until):
        activity = svc.get(42, since, until)

        h_api._api_request.assert_not_called()

        assert activity == {"num_annotations": 0, "courses": []}

    @pytest.fixture
    def since(self):
        """The time that tests will be requesting activity since."""
        return datetime(year=2023, month=2, day=1)

    @pytest.fixture
    def until(self, since):
        """The time that tests will be requesting activity until."""
        return since + timedelta(days=1)

    @pytest.fixture
    def user(self, db_session):
        """The user whose activity the tests will be requesting."""
        user = factories.User()
        db_session.flush()  # Flush the DB to generate user.id.
        return user

    @pytest.fixture
    def h_api(self, h_api):
        h_api._api_request.return_value = {"groups": []}
        return h_api

    @pytest.fixture
    def svc(self, db_session, h_api):
        return EmailDigestsService(db_session, h_api)
