# -*- coding: utf-8 -*-

import pytest
from sqlalchemy.exc import IntegrityError

from lms.models import CourseGroup


@pytest.mark.usefixtures("noise_groups")
class TestCourseGroup:
    def test_get_returns_matching_group(self, db_session):
        db_session.add(
            CourseGroup(
                tool_consumer_instance_guid="TEST_GUID",
                context_id="TEST_CONTEXT",
                pubid="TEST_PUBID",
            )
        )

        group = CourseGroup.get(db_session, "TEST_GUID", "TEST_CONTEXT")

        assert group.tool_consumer_instance_guid == "TEST_GUID"
        assert group.context_id == "TEST_CONTEXT"
        assert group.pubid == "TEST_PUBID"

    def test_get_returns_None_if_no_matching_group(self, db_session):
        assert CourseGroup.get(db_session, "TEST_GUID", "TEST_CONTEXT") is None

    def test_you_cant_save_a_group_with_no_tool_consumer_instance_guid(
        self, db_session
    ):
        db_session.add(CourseGroup(context_id="TEST_CONTEXT", pubid="TEST_PUBID"))

        with pytest.raises(
            IntegrityError,
            match='null value in column "tool_consumer_instance_guid" violates not-null constraint',
        ):
            db_session.flush()

    def test_you_cant_save_a_group_with_no_context_id(self, db_session):
        db_session.add(
            CourseGroup(tool_consumer_instance_guid="TEST_GUID", pubid="TEST_PUBID")
        )

        with pytest.raises(
            IntegrityError,
            match='null value in column "context_id" violates not-null constraint',
        ):
            db_session.flush()

    def test_you_cant_save_a_group_with_no_pubid(self, db_session):
        db_session.add(
            CourseGroup(
                tool_consumer_instance_guid="TEST_GUID", context_id="TEST_CONTEXT"
            )
        )

        with pytest.raises(
            IntegrityError,
            match='null value in column "pubid" violates not-null constraint',
        ):
            db_session.flush()

    def test_you_cant_save_two_groups_with_the_same_tool_consumer_instance_guid_and_context_id(
        self, db_session
    ):
        # Even if they have different pubids, two groups can't have the same
        # tool_consumer_instance_guid and context_id.
        db_session.add_all(
            (
                CourseGroup(
                    tool_consumer_instance_guid="TEST_GUID",
                    context_id="TEST_CONTEXT",
                    pubid="TEST_PUBID_1",
                ),
                CourseGroup(
                    tool_consumer_instance_guid="TEST_GUID",
                    context_id="TEST_CONTEXT",
                    pubid="TEST_PUBID_2",
                ),
            )
        )

        with pytest.raises(
            IntegrityError,
            match='duplicate key value violates unique constraint "ix__course_groups_tool_consumer_instance_guid_context_id"',
        ):
            db_session.flush()

    def test_you_cant_save_two_groups_with_the_same_pubid(self, db_session):
        # Even if they have different tool_consumer_instance_guid's and
        # context_id's, two groups can't have the same pubid.
        db_session.add_all(
            (
                CourseGroup(
                    tool_consumer_instance_guid="TEST_GUID_1",
                    context_id="TEST_CONTEXT_1",
                    pubid="TEST_PUBID",
                ),
                CourseGroup(
                    tool_consumer_instance_guid="TEST_GUID_2",
                    context_id="TEST_CONTEXT_2",
                    pubid="TEST_PUBID",
                ),
            )
        )

        with pytest.raises(
            IntegrityError,
            match='duplicate key value violates unique constraint "uq__course_groups__pubid"',
        ):
            db_session.flush()

    def test_you_can_save_two_groups_with_the_same_tool_consumer_instance_guid(
        self, db_session
    ):
        # As long as they have different context_id's and pubid's you can save
        # two groups with the same tool_consumer_instance_guid.
        db_session.add_all(
            (
                CourseGroup(
                    tool_consumer_instance_guid="TEST_GUID",
                    context_id="TEST_CONTEXT_1",
                    pubid="TEST_PUBID_1",
                ),
                CourseGroup(
                    tool_consumer_instance_guid="TEST_GUID",
                    context_id="TEST_CONTEXT_2",
                    pubid="TEST_PUBID_2",
                ),
            )
        )

        db_session.flush()

    def test_you_can_save_two_groups_with_the_same_context_id(self, db_session):
        # As long as they have different tool_consumer_instance_guid's and
        # pubid's you can save two groups with the same
        # tool_consumer_instance_guid.
        db_session.add_all(
            (
                CourseGroup(
                    tool_consumer_instance_guid="TEST_GUID_1",
                    context_id="TEST_CONTEXT",
                    pubid="TEST_PUBID_1",
                ),
                CourseGroup(
                    tool_consumer_instance_guid="TEST_GUID_3",
                    context_id="TEST_CONTEXT",
                    pubid="TEST_PUBID_2",
                ),
            )
        )

        db_session.flush()

    @pytest.fixture
    def noise_groups(self, db_session):
        # Add some "noise" groups to the DB to make the tests more realistic.
        db_session.add_all(
            (
                CourseGroup(
                    tool_consumer_instance_guid="NOISE_GUID_1",
                    context_id="NOISE_CONTEXT_1",
                    pubid="NOISE_PUBID_1",
                ),
                CourseGroup(
                    tool_consumer_instance_guid="NOISE_GUID_2",
                    context_id="NOISE_CONTEXT_2",
                    pubid="NOISE_PUBID_2",
                ),
            )
        )
        db_session.flush()
