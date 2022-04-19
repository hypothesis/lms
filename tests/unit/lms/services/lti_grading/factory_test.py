from unittest.mock import sentinel

import pytest

from lms.services.lti_grading.factory import service_factory


class TestFactory:
    def test_v11(
        self,
        pyramid_request,
        LTI11GradingService,
        http_service,
        oauth1_service,
    ):
        svc = service_factory(sentinel.context, pyramid_request)

        LTI11GradingService.assert_called_once_with(
            sentinel.grading_url, http_service, oauth1_service
        )
        assert svc == LTI11GradingService.return_value

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "lis_outcome_service_url": sentinel.grading_url
        }
        return pyramid_request

    @pytest.fixture
    def LTI11GradingService(self, patch):
        return patch("lms.services.lti_grading.factory.LTI11GradingService")
