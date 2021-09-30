from unittest.mock import sentinel

import pytest
from sqlalchemy.orm.exc import MultipleResultsFound

from lms.services.assignment import AssignmentService, factory
from tests import factories

MATCHING_TOOL_CONSUMER_INSTANCE_GUID = "matching_tool_consumer_instance_guid"
MATCHING_RESOURCE_LINK_ID = "matching_resource_link_id"
MATCHING_EXT_LTI_ASSIGNMENT_ID = "matching_ext_lti_assignment_id"


class TestGet:
    def test_at_least_one_of_resource_link_id_or_ext_lti_assignment_id_is_required(
        self, svc
    ):
        with pytest.raises(ValueError):
            svc.get(
                sentinel.tool_consumer_instance_guid,
                resource_link_id=None,
                ext_lti_assignment_id=None,
            )

    def test_it_raises_if_there_are_multiple_matching_assignments(self, svc):
        # Create two assignments that will both match the query.
        factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=MATCHING_RESOURCE_LINK_ID,
            ext_lti_assignment_id=None,
        )
        factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=None,
            ext_lti_assignment_id=MATCHING_EXT_LTI_ASSIGNMENT_ID,
        )

        with pytest.raises(MultipleResultsFound):
            svc.get(
                MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
                MATCHING_RESOURCE_LINK_ID,
                MATCHING_EXT_LTI_ASSIGNMENT_ID,
            )

    # If there's an assignment in the DB that has both the matching
    # resource_link_id and the matching ext_lti_assignment_id then get() will
    # find that assignment if called with:
    #
    # 1. The matching resource_link_id and no ext_lti_assignment_id
    # 2. The matching ext_lti_assignment_id and no resource_link_id
    # 3. Both the matching resource_link_id and the matching ext_lti_assignment_id.
    @pytest.mark.parametrize(
        "resource_link_id,ext_lti_assignment_id",
        [
            pytest.param(
                MATCHING_RESOURCE_LINK_ID, None, id="called with resource_link_id only"
            ),
            pytest.param(
                None,
                MATCHING_EXT_LTI_ASSIGNMENT_ID,
                id="called with ext_lti_assignment_id only",
            ),
            pytest.param(
                MATCHING_RESOURCE_LINK_ID,
                MATCHING_EXT_LTI_ASSIGNMENT_ID,
                id="called with both resource_link_id and ext_lti_assignment_id",
            ),
        ],
    )
    def test_it_finds_assignment_with_matching_resource_link_id_and_ext_lti_assignment_id(
        self, svc, resource_link_id, ext_lti_assignment_id
    ):
        matching_assignment = factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=MATCHING_RESOURCE_LINK_ID,
            ext_lti_assignment_id=MATCHING_EXT_LTI_ASSIGNMENT_ID,
        )

        returned_assignment = svc.get(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id,
            ext_lti_assignment_id,
        )

        assert returned_assignment == matching_assignment

    # If there's an assignment in the DB that has the matching resource_link_id
    # and no ext_lti_assignment_id then get() will find that assignment if
    # called with:
    #
    # 1. The matching resource_link_id and no ext_lti_assignment_id
    # 2. The matching resource_link_id and an ext_lti_assignment_id (any value)
    @pytest.mark.parametrize(
        "ext_lti_assignment_id",
        [
            pytest.param(None, id="called with resource_link_id only"),
            pytest.param(
                "any_ext_lti_assignment_id",
                id="called with both resource_link_id and ext_lti_assignment_id",
            ),
        ],
    )
    def test_it_finds_assignment_with_matching_resource_link_id_only(
        self, svc, ext_lti_assignment_id
    ):
        matching_assignment = factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=MATCHING_RESOURCE_LINK_ID,
            ext_lti_assignment_id=None,
        )

        returned_assignment = svc.get(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            MATCHING_RESOURCE_LINK_ID,
            ext_lti_assignment_id,
        )

        assert returned_assignment == matching_assignment

    # If there's an assignment in the DB that has the matching
    # ext_lti_assignment_id and no resource_link_id then get() will find that
    # assignment if called with:
    #
    # 1. The matching ext_lti_assignment_id and no resource_link_id
    # 2. The matching ext_lti_assignment_id and a resource_link_id (any value)
    @pytest.mark.parametrize(
        "resource_link_id",
        [
            pytest.param(
                None,
                id="called with ext_lti_assignment_id only",
            ),
            pytest.param(
                "any_resource_link_id",
                id="called with both resource_link_id and ext_lti_assignment_id",
            ),
        ],
    )
    def test_it_finds_assignment_with_matching_ext_lti_assignment_id_only(
        self, svc, resource_link_id
    ):
        matching_assignment = factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=None,
            ext_lti_assignment_id=MATCHING_EXT_LTI_ASSIGNMENT_ID,
        )

        returned_assignment = svc.get(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id,
            MATCHING_EXT_LTI_ASSIGNMENT_ID,
        )

        assert returned_assignment == matching_assignment

    # If there's no matching assignment in the DB then get() will return None
    # whether called with a resource_link_id, an ext_lti_assignment_id or both.
    @pytest.mark.parametrize(
        "resource_link_id,ext_lti_assignment_id",
        [
            pytest.param(
                MATCHING_RESOURCE_LINK_ID, None, id="called with resource_link_id only"
            ),
            pytest.param(
                None,
                MATCHING_EXT_LTI_ASSIGNMENT_ID,
                id="called with ext_lti_assignment_id only",
            ),
            pytest.param(
                MATCHING_RESOURCE_LINK_ID,
                MATCHING_EXT_LTI_ASSIGNMENT_ID,
                id="called with both resource_link_id and ext_lti_assignment_id",
            ),
        ],
    )
    def test_no_matching_assignment(self, svc, resource_link_id, ext_lti_assignment_id):
        returned_assignment = svc.get(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id,
            ext_lti_assignment_id,
        )

        assert returned_assignment is None

    # If get() is called with both a resource_link_id and an
    # ext_lti_assignment_id it **won't** return an assignment that has:
    #
    # 1. The matching resource_link_id but a different ext_lti_assignment_id
    # 2. Or the matching ext_lti_assignment_id but a different resource_link_id
    @pytest.mark.parametrize(
        "resource_link_id,ext_lti_assignment_id",
        [
            pytest.param(
                MATCHING_RESOURCE_LINK_ID,
                "different",
                id="The assignment's resource_link_id matches but its ext_lti_assignment_id is different",
            ),
            pytest.param(
                "different",
                MATCHING_EXT_LTI_ASSIGNMENT_ID,
                id="The assignment's ext_lti_assignment_id matches but its resource_link_id is different",
            ),
        ],
    )
    def test_assignment_has_one_matching_and_one_different_id(
        self, svc, resource_link_id, ext_lti_assignment_id
    ):
        factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=resource_link_id,
            ext_lti_assignment_id=ext_lti_assignment_id,
        )

        returned_assignment = svc.get(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            MATCHING_RESOURCE_LINK_ID,
            MATCHING_EXT_LTI_ASSIGNMENT_ID,
        )

        assert returned_assignment is None

    # get() never returns an assignment whose tool_consumer_instance_guid doesn't match.
    @pytest.mark.parametrize(
        "resource_link_id,ext_lti_assignment_id",
        [
            pytest.param(
                MATCHING_RESOURCE_LINK_ID,
                None,
                id="called with resource_link_id only",
            ),
            pytest.param(
                None,
                MATCHING_EXT_LTI_ASSIGNMENT_ID,
                id="called with ext_lti_assignment_id only",
            ),
            pytest.param(
                MATCHING_RESOURCE_LINK_ID,
                MATCHING_EXT_LTI_ASSIGNMENT_ID,
                id="called with both resource_link_id and ext_lti_assignment_id",
            ),
        ],
    )
    def test_assignment_has_different_tool_consumer_instance_guid(
        self, svc, resource_link_id, ext_lti_assignment_id
    ):
        factories.Assignment(
            tool_consumer_instance_guid="different",
            resource_link_id=MATCHING_RESOURCE_LINK_ID,
            ext_lti_assignment_id=MATCHING_EXT_LTI_ASSIGNMENT_ID,
        )

        returned_assignment = svc.get(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id,
            ext_lti_assignment_id,
        )

        assert returned_assignment is None


class TestGetForCanvasLaunch:
    @pytest.mark.parametrize(
        "resource_link_id,ext_lti_assignment_id",
        [
            pytest.param(
                None,
                sentinel.ext_lti_assignment_id,
                id="resource_link_id can't be None",
            ),
            pytest.param(
                sentinel.resource_link_id,
                None,
                id="ext_lti_assignment_id can't be None",
            ),
            pytest.param(
                None,
                None,
                id="resource_link_id and ext_lti_assignment_id can't both be None",
            ),
        ],
    )
    def test_resource_link_id_and_ext_lti_assignment_id_cant_be_None(
        self, svc, resource_link_id, ext_lti_assignment_id
    ):
        with pytest.raises(AssertionError):
            svc.get_for_canvas_launch(
                sentinel.tool_consumer_instance_guid,
                resource_link_id,
                ext_lti_assignment_id,
            )

    def test_if_theres_no_matching_assignments_it_returns_an_empty_list(self, svc):
        factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=MATCHING_RESOURCE_LINK_ID,
            ext_lti_assignment_id="different",
        )
        factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id="different",
            ext_lti_assignment_id=MATCHING_EXT_LTI_ASSIGNMENT_ID,
        )
        factories.Assignment(
            tool_consumer_instance_guid="different",
            resource_link_id=MATCHING_RESOURCE_LINK_ID,
            ext_lti_assignment_id=MATCHING_EXT_LTI_ASSIGNMENT_ID,
        )

        assignments = svc.get_for_canvas_launch(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            MATCHING_RESOURCE_LINK_ID,
            MATCHING_EXT_LTI_ASSIGNMENT_ID,
        )

        assert assignments == []

    @pytest.mark.parametrize(
        "resource_link_id,ext_lti_assignment_id",
        [
            pytest.param(
                MATCHING_RESOURCE_LINK_ID,
                None,
                id="assignment with matching resource_link_id only",
            ),
            pytest.param(
                None,
                MATCHING_EXT_LTI_ASSIGNMENT_ID,
                id="assignment with matching ext_lti_assignment_id only",
            ),
            pytest.param(
                MATCHING_RESOURCE_LINK_ID,
                MATCHING_EXT_LTI_ASSIGNMENT_ID,
                id="assignment with matching resource_link_id and ext_lti_assignment_id",
            ),
        ],
    )
    def test_if_theres_one_matching_assignment_it_returns_it(
        self, svc, resource_link_id, ext_lti_assignment_id
    ):
        assignment = factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=resource_link_id,
            ext_lti_assignment_id=ext_lti_assignment_id,
        )

        assignments = svc.get_for_canvas_launch(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            MATCHING_RESOURCE_LINK_ID,
            MATCHING_EXT_LTI_ASSIGNMENT_ID,
        )

        assert assignments == [assignment]

    def test_if_there_are_two_matching_assignments_it_returns_them_both(self, svc):
        matching_assignments = [
            factories.Assignment(
                tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
                resource_link_id=MATCHING_RESOURCE_LINK_ID,
                ext_lti_assignment_id=None,
            ),
            factories.Assignment(
                tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
                resource_link_id=None,
                ext_lti_assignment_id=MATCHING_EXT_LTI_ASSIGNMENT_ID,
            ),
        ]

        returned_assignments = svc.get_for_canvas_launch(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            MATCHING_RESOURCE_LINK_ID,
            MATCHING_EXT_LTI_ASSIGNMENT_ID,
        )

        assert returned_assignments == matching_assignments


class TestExists:
    @pytest.mark.parametrize(
        "resource_link_id,ext_lti_assignment_id",
        [
            (MATCHING_RESOURCE_LINK_ID, None),
            (None, MATCHING_EXT_LTI_ASSIGNMENT_ID),
            (MATCHING_RESOURCE_LINK_ID, MATCHING_EXT_LTI_ASSIGNMENT_ID),
        ],
    )
    def test_if_theres_a_matching_assignment_it_returns_True(
        self, svc, resource_link_id, ext_lti_assignment_id
    ):
        factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=resource_link_id,
            ext_lti_assignment_id=ext_lti_assignment_id,
        )

        result = svc.exists(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id,
            ext_lti_assignment_id,
        )

        assert result is True

    def test_if_there_are_multiple_matching_assignments_it_returns_True(self, svc):
        factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=MATCHING_RESOURCE_LINK_ID,
            ext_lti_assignment_id=None,
        )
        factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=None,
            ext_lti_assignment_id=MATCHING_EXT_LTI_ASSIGNMENT_ID,
        )

        result = svc.exists(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            MATCHING_RESOURCE_LINK_ID,
            MATCHING_EXT_LTI_ASSIGNMENT_ID,
        )

        assert result is True

    @pytest.mark.parametrize(
        "resource_link_id,ext_lti_assignment_id",
        [
            (MATCHING_RESOURCE_LINK_ID, None),
            (None, MATCHING_EXT_LTI_ASSIGNMENT_ID),
            (MATCHING_RESOURCE_LINK_ID, MATCHING_EXT_LTI_ASSIGNMENT_ID),
        ],
    )
    def test_if_there_are_no_matching_assignments_it_returns_False(
        self, svc, resource_link_id, ext_lti_assignment_id
    ):
        result = svc.exists(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id,
            ext_lti_assignment_id,
        )

        assert not result

    def test_if_both_resource_link_id_and_ext_lti_assignment_id_are_None_it_returns_False(
        self, svc
    ):
        result = svc.exists(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            None,
            None,
        )

        assert not result


class TestSetDocumentURL:
    def test_at_least_one_of_resource_link_id_or_ext_lti_assignment_id_is_required(
        self, svc
    ):
        with pytest.raises(ValueError):
            svc.set_document_url(
                "new_document_url", MATCHING_TOOL_CONSUMER_INSTANCE_GUID
            )

    def test_it_raises_if_there_are_multiple_matching_assignments(self, svc):
        factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=MATCHING_RESOURCE_LINK_ID,
            ext_lti_assignment_id=None,
        )
        factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=None,
            ext_lti_assignment_id=MATCHING_EXT_LTI_ASSIGNMENT_ID,
        )

        with pytest.raises(MultipleResultsFound):
            svc.set_document_url(
                "new_document_url",
                MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
                MATCHING_RESOURCE_LINK_ID,
                MATCHING_EXT_LTI_ASSIGNMENT_ID,
            )

    @pytest.mark.parametrize(
        "resource_link_id,ext_lti_assignment_id",
        [
            (MATCHING_RESOURCE_LINK_ID, None),
            (None, MATCHING_EXT_LTI_ASSIGNMENT_ID),
            (MATCHING_RESOURCE_LINK_ID, MATCHING_EXT_LTI_ASSIGNMENT_ID),
        ],
    )
    def test_if_theres_no_matching_assignment_it_creates_one(
        self, svc, resource_link_id, ext_lti_assignment_id
    ):
        svc.set_document_url(
            "new_document_url",
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id,
            ext_lti_assignment_id,
        )

        assert (
            svc.get(
                MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
                resource_link_id,
                ext_lti_assignment_id,
            ).document_url
            == "new_document_url"
        )

    @pytest.mark.parametrize(
        "resource_link_id,ext_lti_assignment_id",
        [
            (MATCHING_RESOURCE_LINK_ID, None),
            (None, MATCHING_EXT_LTI_ASSIGNMENT_ID),
            (MATCHING_RESOURCE_LINK_ID, MATCHING_EXT_LTI_ASSIGNMENT_ID),
        ],
    )
    def test_if_theres_a_matching_assignment_it_updates_it(
        self, svc, resource_link_id, ext_lti_assignment_id
    ):
        factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=resource_link_id,
            ext_lti_assignment_id=ext_lti_assignment_id,
            document_url="old_document_url",
        )

        svc.set_document_url(
            "new_document_url",
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id,
            ext_lti_assignment_id,
        )

        assert (
            svc.get(
                MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
                resource_link_id,
                ext_lti_assignment_id,
            ).document_url
            == "new_document_url"
        )


class TestMergeCanvasAssignments:
    @pytest.mark.parametrize(
        "old_extra,merged_extra",
        [
            ({}, {}),
            ({"somedata": "not copied"}, {}),
            ({"canvas_file_mappings": {1: 2}}, {"canvas_file_mappings": {1: 2}}),
        ],
    )
    def test_it(
        self,
        old_extra,
        merged_extra,
        svc,
        db_session,
    ):
        old_assignment = factories.Assignment(
            resource_link_id="resource_link_id",
            ext_lti_assignment_id=None,
            extra=old_extra,
        )
        new_assignment = factories.Assignment(
            tool_consumer_instance_guid=old_assignment.tool_consumer_instance_guid,
            resource_link_id=None,
            ext_lti_assignment_id="ext_lti_assignment_id",
            extra={},
        )
        db_session.flush()

        merged_assignment = svc.merge_canvas_assignments(old_assignment, new_assignment)

        assert merged_assignment.id == new_assignment.id
        assert merged_assignment.resource_link_id == old_assignment.resource_link_id
        assert (
            merged_assignment.ext_lti_assignment_id
            == new_assignment.ext_lti_assignment_id
        )
        assert merged_assignment.extra == merged_extra
        assert (
            svc.get(
                old_assignment.tool_consumer_instance_guid,
                old_assignment.resource_link_id,
                new_assignment.ext_lti_assignment_id,
            )
            == merged_assignment
        )


class TestFactory:
    def test_it(self, pyramid_request):
        assignment_service = factory(sentinel.context, pyramid_request)

        assert isinstance(assignment_service, AssignmentService)


@pytest.fixture(autouse=True)
def noise():
    factories.Assignment(
        tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
        resource_link_id="noise_resource_link_id",
        ext_lti_assignment_id="noise_ext_lti_assignment_id",
    )
    factories.Assignment(
        tool_consumer_instance_guid="noise_tool_consumer_instance_guid",
        resource_link_id=MATCHING_RESOURCE_LINK_ID,
        ext_lti_assignment_id=MATCHING_EXT_LTI_ASSIGNMENT_ID,
    )


@pytest.fixture
def svc(db_session):
    return AssignmentService(db_session)
