import pytest

from lms.services import includeme
from lms.services.application_instance_getter import (
    application_instance_getter_service_factory,
)
from lms.services.canvas_api import canvas_api_client_factory
from lms.services.grading_info import GradingInfoService
from lms.services.group_info import GroupInfoService
from lms.services.h_api import HAPI
from lms.services.launch_verifier import LaunchVerifier
from lms.services.lti_h import LTIHService
from lms.services.lti_outcomes import LTIOutcomesClient
from lms.services.oauth1 import OAuth1Service
from lms.services.vitalsource import VitalSourceService


class TestIncludeme:
    @pytest.mark.parametrize(
        "name,service_class",
        (
            ("ai_getter", application_instance_getter_service_factory),
            ("canvas_api_client", canvas_api_client_factory),
            ("h_api", HAPI),
            ("launch_verifier", LaunchVerifier),
            ("grading_info", GradingInfoService),
            ("lti_outcomes_client", LTIOutcomesClient),
            ("group_info", GroupInfoService),
            ("lti_h", LTIHService),
            ("oauth1", OAuth1Service),
            ("vitalsource", VitalSourceService),
        ),
    )
    def test_it_has_the_expected_service(self, name, service_class, pyramid_config):
        includeme(pyramid_config)

        assert pyramid_config.find_service_factory(name=name) == service_class
