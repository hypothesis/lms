from unittest.mock import Mock, sentinel

import pytest

from lms.services.lti_grading.factory import service_factory


class TestFactory:
    def test_v11(
        self,
        pyramid_request,
        application_instance_service,
        LTI11GradingService,
        http_service,
        oauth1_service,
    ):
        application_instance_service.get_current.return_value = Mock(lti_version="1.1")

        svc = service_factory(sentinel.context, pyramid_request)

        LTI11GradingService.assert_called_once_with(
            sentinel.grading_url, http_service, oauth1_service
        )
        assert svc == LTI11GradingService.return_value

    def test_v13(
        self,
        pyramid_request,
        LTI13GradingService,
        application_instance_service,
        ltia_http_service,
    ):
        application_instance_service.get_current.return_value = Mock(
            lti_version="1.3.0"
        )

        svc = service_factory(sentinel.context, pyramid_request)

        LTI13GradingService.assert_called_once_with(
            sentinel.grading_url, sentinel.lineitems, ltia_http_service
        )
        assert svc == LTI13GradingService.return_value

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "lis_outcome_service_url": sentinel.grading_url
        }
        pyramid_request.lti_params = {"lineitems": sentinel.lineitems}

        return pyramid_request

    @pytest.fixture
    def LTI11GradingService(self, patch):
        return patch("lms.services.lti_grading.factory.LTI11GradingService")

    @pytest.fixture
    def LTI13GradingService(self, patch):
        return patch("lms.services.lti_grading.factory.LTI13GradingService")
