from unittest import mock

import pytest

from lms.models import ApplicationInstance, LISResultSourcedId
from lms.resources import LTILaunchResource
from lms.services.lis_result_sourcedid import LISResultSourcedIdService
from lms import values


class TestLISResultSourcedIdUpsert:
    def test_it_creates_new_record_if_no_matching_exists(
        self, svc, lis_result_sourcedid_info, h_user, lti_user, db_session
    ):
        lis_result_sourcedid = svc.upsert(lis_result_sourcedid_info, h_user, lti_user)

        persisted_lis_result_sourcedid = db_session.query(LISResultSourcedId).one()

        assert isinstance(lis_result_sourcedid, LISResultSourcedId)
        assert persisted_lis_result_sourcedid is lis_result_sourcedid
        assert db_session.query(LISResultSourcedId).count() == 1

    def test_it_sets_values_from_lis_info_when_new_record(
        self, svc, lis_result_sourcedid_info, h_user, lti_user, db_session
    ):
        lis_result_sourcedid = svc.upsert(lis_result_sourcedid_info, h_user, lti_user)

        for field in lis_result_sourcedid_info._fields:
            assert getattr(lis_result_sourcedid, field) == getattr(
                lis_result_sourcedid_info, field
            )

    def test_it_sets_values_from_h_user_when_new_record(
        self, svc, lis_result_sourcedid_info, h_user, lti_user, db_session
    ):
        lis_result_sourcedid = svc.upsert(lis_result_sourcedid_info, h_user, lti_user)

        assert lis_result_sourcedid.h_username == h_user.username
        assert lis_result_sourcedid.h_display_name == h_user.display_name

    def test_it_sets_values_from_lti_user_when_new_record(
        self, svc, lis_result_sourcedid_info, h_user, lti_user, db_session
    ):
        lis_result_sourcedid = svc.upsert(lis_result_sourcedid_info, h_user, lti_user)

        assert lis_result_sourcedid.oauth_consumer_key == lti_user.oauth_consumer_key
        assert lis_result_sourcedid.user_id == lti_user.user_id

    def test_it_updates_existing_record_if_matching_exists(
        self,
        svc,
        lis_result_sourcedid_info,
        h_user,
        lti_user,
        lis_result_sourcedid,
        db_session,
    ):
        # Update a couple of attributes on the model...
        h_user2 = h_user._replace(display_name="Someone Else")
        lis_result_sourcedid_info_2 = lis_result_sourcedid_info._replace(
            lis_result_sourcedid="something different"
        )
        # Note: Both fields from ``LTIUser`` would always be the same in any matching record

        lis_result_sourcedid_updated = svc.upsert(
            lis_result_sourcedid_info_2, h_user2, lti_user
        )

        assert lis_result_sourcedid_updated is lis_result_sourcedid
        assert (
            lis_result_sourcedid_updated.lis_result_sourcedid == "something different"
        )
        assert lis_result_sourcedid.h_display_name == "Someone Else"

    @pytest.fixture
    def lti_user(self):
        return values.LTIUser("TEST_USER_ID", "TEST_OAUTH_CONSUMER_KEY", "TEST_ROLES")

    @pytest.fixture
    def h_user(self):
        return values.HUser(authority="TEST_AUTHORITY", username="seanh")

    @pytest.fixture
    def application_instance(self, db_session):
        """The ApplicationInstance that the LISResultSourcedIds belong to"""
        application_instance = ApplicationInstance(
            consumer_key="test_consumer_key",
            shared_secret="test_shared_secret",
            lms_url="test_lms_url",
            requesters_email="test_requesters_email",
        )
        db_session.add(application_instance)
        return application_instance

    @pytest.fixture
    def context(self, h_user):
        context = mock.create_autospec(
            LTILaunchResource, spec_set=True, instance=True, h_user=h_user
        )
        return context

    @pytest.fixture
    def svc(self, context, pyramid_request):
        return LISResultSourcedIdService(context, pyramid_request)

    @pytest.fixture
    def lis_result_sourcedid_info(self, application_instance):
        return values.LISResultSourcedId(
            lis_result_sourcedid="result_sourcedid",
            lis_outcome_service_url="https://somewhere.else",
            context_id="random context",
            resource_link_id="random resource link id",
            tool_consumer_info_product_family_code="BlackboardLearn",
        )

    @pytest.fixture
    def lis_result_sourcedid(
        self, lis_result_sourcedid_info, h_user, lti_user, db_session
    ):
        lis_result_sourcedid_ = LISResultSourcedId()
        lis_result_sourcedid_.lis_result_sourcedid = (
            lis_result_sourcedid_info.lis_result_sourcedid
        )
        lis_result_sourcedid_.lis_outcome_service_url = (
            lis_result_sourcedid_info.lis_outcome_service_url
        )
        lis_result_sourcedid_.context_id = lis_result_sourcedid_info.context_id
        lis_result_sourcedid_.resource_link_id = (
            lis_result_sourcedid_info.resource_link_id
        )
        lis_result_sourcedid_.tool_consumer_info_product_family_code = (
            lis_result_sourcedid_info.tool_consumer_info_product_family_code
        )
        lis_result_sourcedid_.h_username = h_user.username
        lis_result_sourcedid_.h_display_name = h_user.display_name
        lis_result_sourcedid_.oauth_consumer_key = lti_user.oauth_consumer_key
        lis_result_sourcedid_.user_id = lti_user.user_id

        db_session.add(lis_result_sourcedid_)
        return lis_result_sourcedid_
