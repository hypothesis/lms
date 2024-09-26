import pytest
from h_matchers import Any

from lms.services import includeme
from lms.services.canvas_api import canvas_api_client_factory
from lms.services.grading_info import GradingInfoService
from lms.services.group_info import GroupInfoService
from lms.services.h_api import HAPI
from lms.services.launch_verifier import LaunchVerifier
from lms.services.lti_h import LTIHService


class TestIncludeme:
    @pytest.mark.parametrize(
        "name,service_class",
        (
            ("canvas_api_client", canvas_api_client_factory),
            ("launch_verifier", LaunchVerifier),
            ("grading_info", GradingInfoService),
            ("group_info", GroupInfoService),
            ("lti_h", LTIHService),
        ),
    )
    def test_it_has_the_expected_service_by_name(
        self, name, service_class, pyramid_config
    ):
        assert pyramid_config.find_service_factory(name=name) == service_class

    @pytest.mark.parametrize("service_class", (HAPI,))
    def test_it_has_the_expected_service(self, service_class, pyramid_request):
        assert pyramid_request.find_service(service_class) == Any.instance_of(
            service_class
        )

    @pytest.fixture(autouse=True)
    def with_services_loaded(self, pyramid_config):
        includeme(pyramid_config)
