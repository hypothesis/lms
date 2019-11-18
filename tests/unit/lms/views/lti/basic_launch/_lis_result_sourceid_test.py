from unittest import mock

import pytest

from lms import values
from lms.resources import LTILaunchResource
from lms.services.lis_result_sourcedid import LISResultSourcedIdService
from lms.validation import ValidationError
from lms.views.lti.basic_launch import BasicLTILaunchViews


@pytest.mark.usefixtures("lis_result_sourcedid_svc")
class TestUpsertLISResultSourcedId:
    def test_it_returns_when_validation_fails(
        self,
        context,
        pyramid_request,
        LISResultSourcedIdSchema,
        lis_result_sourcedid_svc,
    ):
        LISResultSourcedIdSchema.return_value.lis_result_sourcedid_info.side_effect = ValidationError(
            "foo"
        )

        BasicLTILaunchViews._upsert_lis_result_sourcedid(context, pyramid_request)

        LISResultSourcedIdSchema.return_value.lis_result_sourcedid_info.assert_called_once()
        lis_result_sourcedid_svc.upsert.assert_not_called()

    def test_it_raises_if_validation_raises_other_than_ValidationError(
        self,
        context,
        pyramid_request,
        LISResultSourcedIdSchema,
        lis_result_sourcedid_svc,
    ):
        LISResultSourcedIdSchema.return_value.lis_result_sourcedid_info.side_effect = TypeError(
            "foo"
        )

        with pytest.raises(TypeError, match="foo"):
            BasicLTILaunchViews._upsert_lis_result_sourcedid(context, pyramid_request)

        lis_result_sourcedid_svc.upsert.assert_not_called()

    def test_it_does_nothing_if_user_is_instructor(
        self,
        pyramid_request,
        context,
        LISResultSourcedIdSchema,
        lis_result_sourcedid_svc,
        return_value,
    ):
        pyramid_request.lti_user = values.LTIUser(
            "TEST_USER_ID", "TEST_OAUTH_CONSUMER_KEY", "instructor"
        )
        LISResultSourcedIdSchema.return_value.lis_result_sourcedid_info.return_value = (
            return_value
        )

        BasicLTILaunchViews._upsert_lis_result_sourcedid(context, pyramid_request)

        LISResultSourcedIdSchema(
            pyramid_request
        ).lis_result_sourcedid_info.assert_not_called()

        lis_result_sourcedid_svc.upsert.assert_not_called()

    def test_it_upserts_lis_result_sourcedid(
        self,
        pyramid_request,
        context,
        LISResultSourcedIdSchema,
        lis_result_sourcedid_svc,
        return_value,
    ):
        LISResultSourcedIdSchema.return_value.lis_result_sourcedid_info.return_value = (
            return_value
        )

        BasicLTILaunchViews._upsert_lis_result_sourcedid(context, pyramid_request)

        lis_result_sourcedid_svc.upsert.assert_called_once_with(
            return_value, context.h_user, pyramid_request.lti_user
        )

    def test_it_raises_if_upsert_service_raises(
        self,
        pyramid_request,
        context,
        LISResultSourcedIdSchema,
        lis_result_sourcedid_svc,
        return_value,
    ):
        LISResultSourcedIdSchema.return_value.lis_result_sourcedid_info.return_value = (
            return_value
        )
        lis_result_sourcedid_svc.upsert.side_effect = TypeError("service raised")
        with pytest.raises(TypeError, match="service raised"):
            BasicLTILaunchViews._upsert_lis_result_sourcedid(context, pyramid_request)

        lis_result_sourcedid_svc.upsert.assert_called_once()

    @pytest.fixture
    def context(self):
        context = mock.create_autospec(
            LTILaunchResource,
            spec_set=True,
            instance=True,
            h_user=values.HUser(
                authority="TEST_AUTHORITY",
                username="test_username",
                display_name="test_display_name",
            ),
        )
        return context

    @pytest.fixture
    def return_value(self):
        return values.LISResultSourcedId(
            lis_result_sourcedid="TEST LIS RESULT SOURCEDID",
            lis_outcome_service_url="TEST LIS OUTCOME SERVICE URL",
            context_id="TEST CONTEXT ID",
            resource_link_id="TEST RESOURCE LINK ID",
            tool_consumer_info_product_family_code="FooLMS",
        )

    @pytest.fixture
    def lis_result_sourcedid_svc(self, pyramid_config):
        svc = mock.create_autospec(
            LISResultSourcedIdService, spec_set=True, instance=True
        )
        pyramid_config.register_service(svc, name="lis_result_sourcedid")
        return svc

    @pytest.fixture
    def LISResultSourcedIdSchema(self, patch):
        return patch("lms.views.lti.basic_launch.LISResultSourcedIdSchema")
