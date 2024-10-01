from unittest.mock import Mock, sentinel

import pytest

from lms.services.lti_grading.factory import (
    LTI11GradingService,
    LTI13GradingService,
    service_factory,
)


class TestFactory:
    def test_v11(
        self, pyramid_request, LTI11GradingService, http_service, oauth1_service
    ):
        pyramid_request.lti_user.application_instance = Mock(lti_version="1.1")

        svc = service_factory(sentinel.context, pyramid_request)

        LTI11GradingService.assert_called_once_with(
            sentinel.grading_url,
            http_service,
            oauth1_service,
            pyramid_request.lti_user.application_instance,
        )
        assert svc == LTI11GradingService.return_value

    def test_v13(
        self, pyramid_request, LTI13GradingService, ltia_http_service, misc_plugin
    ):
        pyramid_request.lti_user.application_instance = Mock(lti_version="1.3.0")

        svc = service_factory(sentinel.context, pyramid_request)

        LTI13GradingService.assert_called_once_with(
            sentinel.grading_url,
            sentinel.lineitems,
            ltia_http_service,
            pyramid_request.product.family,
            misc_plugin,
            pyramid_request.lti_user.application_instance.lti_registration,
        )
        assert svc == LTI13GradingService.return_value

    def test_v13_line_item_url_from_lti_params(
        self, pyramid_request, LTI13GradingService, ltia_http_service, misc_plugin
    ):
        del pyramid_request.parsed_params["lis_outcome_service_url"]
        pyramid_request.lti_user.application_instance = Mock(lti_version="1.3.0")

        svc = service_factory(sentinel.context, pyramid_request)

        LTI13GradingService.assert_called_once_with(
            sentinel.grading_url,
            sentinel.lineitems,
            ltia_http_service,
            pyramid_request.product.family,
            misc_plugin,
            pyramid_request.lti_user.application_instance.lti_registration,
        )
        assert svc == LTI13GradingService.return_value

    @pytest.mark.usefixtures("ltia_http_service", "misc_plugin")
    def test_with_explicit_lti_v13_application_instance(
        self, pyramid_request, lti_v13_application_instance
    ):
        svc = service_factory(
            sentinel.context, pyramid_request, lti_v13_application_instance
        )

        assert isinstance(svc, LTI13GradingService)

    @pytest.mark.usefixtures("http_service", "oauth1_service")
    def test_with_explicit_lti_v11_application_instance(
        self, pyramid_request, application_instance
    ):
        svc = service_factory(sentinel.context, pyramid_request, application_instance)

        assert isinstance(svc, LTI11GradingService)

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
