from unittest import mock

import pytest

from lms.models import ApplicationInstance, LISResultSourcedId
from lms.resources import LTILaunchResource
from lms.services.lis_result_sourcedid import LISResultSourcedIdService
from lms.values import HUser


class TestLISResultSourcedIdUpsert:
    def test_it_creates_new_record_if_no_matching_exists(
        self, svc, validated_attrs, db_session
    ):
        lis_result_sourcedid = svc.upsert(validated_attrs)

        persisted_lis_result_sourcedid = db_session.query(LISResultSourcedId).one()

        assert isinstance(lis_result_sourcedid, LISResultSourcedId)
        assert persisted_lis_result_sourcedid is lis_result_sourcedid
        assert db_session.query(LISResultSourcedId).count() == 1

    def test_it_sets_values_from_validated_attrs_when_new_record(
        self, svc, validated_attrs, db_session
    ):
        lis_result_sourcedid = svc.upsert(validated_attrs)

        for key in validated_attrs:
            assert getattr(lis_result_sourcedid, key) == validated_attrs[key]

    def test_it_updates_existing_record_if_matching_exists(
        self, svc, validated_attrs, lis_result_sourcedid, db_session
    ):
        validated_attrs["lis_result_sourcedid"] = "Something entirely different"

        lis_result_sourcedid_updated = svc.upsert(validated_attrs)

        assert lis_result_sourcedid_updated is lis_result_sourcedid
        assert (
            lis_result_sourcedid_updated.lis_result_sourcedid
            == "Something entirely different"
        )

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
    def context(self):
        context = mock.create_autospec(
            LTILaunchResource,
            spec_set=True,
            instance=True,
            h_user=HUser(authority="TEST_AUTHORITY", username="seanh"),
        )
        return context

    @pytest.fixture
    def svc(self, context, pyramid_request):
        return LISResultSourcedIdService(context, pyramid_request)

    @pytest.fixture
    def validated_attrs(self, application_instance):
        return {
            "lis_result_sourcedid": "result_sourcedid",
            "lis_outcome_service_url": "https://somewhere.else",
            "oauth_consumer_key": application_instance.consumer_key,
            "user_id": "339483948",
            "context_id": "random context",
            "resource_link_id": "random resource link id",
            "tool_consumer_info_product_family_code": "BlackboardLearn",
            "h_username": "seanh",
            "h_display_name": "Black Board User",
        }

    @pytest.fixture
    def lis_result_sourcedid(self, validated_attrs, db_session):
        lis_result_sourcedid_ = LISResultSourcedId(**validated_attrs)
        db_session.add(lis_result_sourcedid_)
        return lis_result_sourcedid_
