import pytest
from pyramid.httpexceptions import HTTPUnprocessableEntity

from lms.validation import LISResultSourcedIdSchema
from lms.values import LISResultSourcedId as LISResultSourcedIdValue


class TestLISResultSourcedIdSchema:
    def test_it_parses_params_from_request(self, schema):
        lis_result_sourcedid = schema.parse()

        assert lis_result_sourcedid == {
            "lis_result_sourcedid": "TEST LIS RESULT SOURCEDID",
            "resource_link_id": "TEST RESOURCE LINK ID",
            "lis_outcome_service_url": "TEST LIS OUTCOME SERVICE URL",
            "context_id": "TEST CONTEXT ID",
            "tool_consumer_info_product_family_code": "TEST PRODUCT FAMILY CODE",
        }

    def test_it_does_not_raise_if_optional_field_missing(
        self, pyramid_outcome_request, schema
    ):
        del pyramid_outcome_request.POST["tool_consumer_info_product_family_code"]

        lis_result_sourcedid = schema.parse()

        assert lis_result_sourcedid == {
            "tool_consumer_info_product_family_code": "",
            "lis_result_sourcedid": "TEST LIS RESULT SOURCEDID",
            "resource_link_id": "TEST RESOURCE LINK ID",
            "lis_outcome_service_url": "TEST LIS OUTCOME SERVICE URL",
            "context_id": "TEST CONTEXT ID",
        }

    @pytest.mark.parametrize(
        "missing_param",
        [
            "lis_result_sourcedid",
            "resource_link_id",
            "lis_outcome_service_url",
            "context_id",
            "resource_link_id",
        ],
    )
    def test_it_raises_if_a_required_param_is_missing(
        self, missing_param, pyramid_outcome_request, schema
    ):
        del pyramid_outcome_request.POST[missing_param]

        with pytest.raises(HTTPUnprocessableEntity) as exc_info:
            schema.parse()

        assert exc_info.value.messages == dict(
            [(missing_param, ["Missing data for required field."])]
        )

    def test_it_returns_lis_result_sourcedid_info(self, schema):
        lis_result_sourcedid = schema.lis_result_sourcedid_info()

        assert isinstance(lis_result_sourcedid, LISResultSourcedIdValue)

    def test_it_lis_result_sourcedid_info_does_not_raise_with_missing_optional_field(
        self, schema, pyramid_outcome_request
    ):
        del pyramid_outcome_request.POST["tool_consumer_info_product_family_code"]

        lis_result_sourcedid = schema.lis_result_sourcedid_info()

        assert isinstance(lis_result_sourcedid, LISResultSourcedIdValue)

    @pytest.fixture
    def pyramid_outcome_request(self, pyramid_request):
        """Pyramid ``request`` with needed params for valid outcome record."""
        pyramid_request.POST.update(
            {
                "lis_result_sourcedid": "TEST LIS RESULT SOURCEDID",
                "lis_outcome_service_url": "TEST LIS OUTCOME SERVICE URL",
                "context_id": "TEST CONTEXT ID",
                "resource_link_id": "TEST RESOURCE LINK ID",
                "tool_consumer_info_product_family_code": "TEST PRODUCT FAMILY CODE",
            }
        )
        return pyramid_request

    @pytest.fixture
    def schema(self, pyramid_outcome_request):
        return LISResultSourcedIdSchema(pyramid_outcome_request)
