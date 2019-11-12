from unittest import mock

import pytest

from lms import values
from lms.resources import LTILaunchResource
from lms.services.lis_result_sourcedid import LISResultSourcedIdService
from lms.validation import ValidationError
from lms.views import decorators


@pytest.mark.usefixtures("lis_result_sourcedid_svc")
class TestUpsertLISResultSourcedId:
    def test_it_continues_to_wrapped_fn_if_validation_raises_ValidationError(
        self,
        upsert_lis_result_sourcedid,
        context,
        pyramid_request,
        wrapped,
        LISResultSourcedIdSchema,
        lis_result_sourcedid_svc,
    ):
        LISResultSourcedIdSchema.return_value.lis_result_sourcedid_info.side_effect = ValidationError(
            "foo"
        )

        returned = upsert_lis_result_sourcedid(context, pyramid_request)

        assert returned == wrapped.return_value
        LISResultSourcedIdSchema.return_value.lis_result_sourcedid_info.assert_called_once()
        lis_result_sourcedid_svc.upsert.assert_not_called()
        wrapped.assert_called_once_with(context, pyramid_request)

    def test_it_raises_if_validation_raises_other_than_ValidationError(
        self,
        upsert_lis_result_sourcedid,
        context,
        pyramid_request,
        wrapped,
        LISResultSourcedIdSchema,
        lis_result_sourcedid_svc,
    ):
        LISResultSourcedIdSchema.return_value.lis_result_sourcedid_info.side_effect = TypeError(
            "foo"
        )

        with pytest.raises(TypeError, match="foo"):
            upsert_lis_result_sourcedid(context, pyramid_request)

        lis_result_sourcedid_svc.upsert.assert_not_called()
        wrapped.assert_not_called()

    def test_it_continues_to_wrapped_fn_if_user_is_instructor(
        self,
        upsert_lis_result_sourcedid,
        pyramid_request,
        context,
        wrapped,
        LISResultSourcedIdSchema,
        lis_result_sourcedid_svc,
        lis_result_sourcedid_value,
    ):
        pyramid_request.lti_user = values.LTIUser(
            "TEST_USER_ID", "TEST_OAUTH_CONSUMER_KEY", "instructor"
        )
        LISResultSourcedIdSchema.return_value.lis_result_sourcedid_info.return_value = (
            lis_result_sourcedid_value
        )

        upsert_lis_result_sourcedid(context, pyramid_request)

        LISResultSourcedIdSchema(
            pyramid_request
        ).lis_result_sourcedid_info.assert_called_once()
        wrapped.assert_called_once_with(context, pyramid_request)
        lis_result_sourcedid_svc.upsert.assert_not_called()

    def test_it_continues_to_wrapped_fn_if_LMS_not_blackboard_or_moodle(
        self,
        upsert_lis_result_sourcedid,
        pyramid_request,
        context,
        lis_result_sourcedid_svc,
        LISResultSourcedIdSchema,
        lis_result_sourcedid_value,
        wrapped,
    ):
        lis_result_sourcedid_value = lis_result_sourcedid_value._replace(
            tool_consumer_info_product_family_code="NOT_BLACKBOARD_OR_MOODLE"
        )
        LISResultSourcedIdSchema.return_value.lis_result_sourcedid_info.return_value = (
            lis_result_sourcedid_value
        )

        upsert_lis_result_sourcedid(context, pyramid_request)

        LISResultSourcedIdSchema(
            pyramid_request
        ).lis_result_sourcedid_info.assert_called_once()
        wrapped.assert_called_once_with(context, pyramid_request)
        lis_result_sourcedid_svc.upsert.assert_not_called()

    @pytest.mark.parametrize("product_family_code", ["BlackboardLearn", "moodle"])
    def test_it_upserts_lis_result_sourcedid_if_LMS_is_blackboard_or_moodle(
        self,
        upsert_lis_result_sourcedid,
        pyramid_request,
        context,
        wrapped,
        LISResultSourcedIdSchema,
        lis_result_sourcedid_svc,
        lis_result_sourcedid_value,
        product_family_code,
    ):
        lis_result_sourcedid_value = lis_result_sourcedid_value._replace(
            tool_consumer_info_product_family_code=product_family_code
        )
        LISResultSourcedIdSchema.return_value.lis_result_sourcedid_info.return_value = (
            lis_result_sourcedid_value
        )

        upsert_lis_result_sourcedid(context, pyramid_request)

        lis_result_sourcedid_svc.upsert.assert_called_once_with(
            lis_result_sourcedid_value, context.h_user, pyramid_request.lti_user
        )
        wrapped.assert_called_once_with(context, pyramid_request)

    def test_it_raises_if_upsert_service_raises(
        self,
        upsert_lis_result_sourcedid,
        pyramid_request,
        context,
        wrapped,
        LISResultSourcedIdSchema,
        lis_result_sourcedid_svc,
        lis_result_sourcedid_value,
    ):
        lis_result_sourcedid_value = lis_result_sourcedid_value._replace(
            tool_consumer_info_product_family_code="moodle"
        )
        LISResultSourcedIdSchema.return_value.lis_result_sourcedid_info.return_value = (
            lis_result_sourcedid_value
        )
        lis_result_sourcedid_svc.upsert.side_effect = TypeError("service raised")
        with pytest.raises(TypeError, match="service raised"):
            upsert_lis_result_sourcedid(context, pyramid_request)

        wrapped.assert_not_called()
        lis_result_sourcedid_svc.upsert.assert_called_once()


@pytest.fixture
def context():
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
def lis_result_sourcedid_value():
    return values.LISResultSourcedId(
        lis_result_sourcedid="TEST LIS RESULT SOURCEDID",
        lis_outcome_service_url="TEST LIS OUTCOME SERVICE URL",
        context_id="TEST CONTEXT ID",
        resource_link_id="TEST RESOURCE LINK ID",
        tool_consumer_info_product_family_code="FooLMS",
    )


@pytest.fixture
def wrapped():
    """The wrapped view callable."""

    def view_callable_spec(context, request):
        """Spec for the mock view callable."""

    return mock.create_autospec(view_callable_spec, spec_set=True)


@pytest.fixture
def lis_result_sourcedid_svc(pyramid_config):
    svc = mock.create_autospec(LISResultSourcedIdService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name="lis_result_sourcedid")
    return svc


@pytest.fixture
def upsert_lis_result_sourcedid(wrapped):
    # Return the actual wrapper function so that tests can call it directly.
    return decorators.upsert_lis_result_sourcedid(wrapped)


@pytest.fixture
def LISResultSourcedIdSchema(patch):
    return patch("lms.views.decorators.lis_result_sourcedid.LISResultSourcedIdSchema")
