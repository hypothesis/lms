from unittest.mock import Mock, sentinel

import pytest

from lms.services.lti_grading.factory import service_factory


class TestFactory:
    def test_v11(
        self, pyramid_request, LTI11GradingService, http_service, oauth1_service
    ):
        pyramid_request.lti_user.application_instance = Mock(lti_version="1.1")

        svc = service_factory(sentinel.context, pyramid_request)

        LTI11GradingService.assert_called_once_with(
            sentinel.grading_url, http_service, oauth1_service
        )
        assert svc == LTI11GradingService.return_value

    def test_v13(self, pyramid_request, LTI13GradingService, ltia_http_service):
        pyramid_request.lti_user.application_instance = Mock(lti_version="1.3.0")

        svc = service_factory(sentinel.context, pyramid_request)

        LTI13GradingService.assert_called_once_with(
            sentinel.grading_url,
            sentinel.lineitems,
            ltia_http_service,
            pyramid_request.product.family,
        )
        assert svc == LTI13GradingService.return_value

    def test_v13_line_item_url_from_lti_params(
        self, pyramid_request, LTI13GradingService, ltia_http_service
    ):
        del pyramid_request.parsed_params["lis_outcome_service_url"]
        pyramid_request.lti_user.application_instance = Mock(lti_version="1.3.0")

        svc = service_factory(sentinel.context, pyramid_request)

        LTI13GradingService.assert_called_once_with(
            sentinel.grading_url,
            sentinel.lineitems,
            ltia_http_service,
            pyramid_request.product.family,
        )
        assert svc == LTI13GradingService.return_value

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "lis_outcome_service_url": sentinel.grading_url
        }
        pyramid_request.lti_params = {
            "lineitems": sentinel.lineitems,
            "lis_outcome_service_url": sentinel.grading_url,
        }

        return pyramid_request

    @pytest.fixture
    def LTI11GradingService(self, patch):
        return patch("lms.services.lti_grading.factory.LTI11GradingService")

    @pytest.fixture
    def LTI13GradingService(self, patch):
        return patch("lms.services.lti_grading.factory.LTI13GradingService")
