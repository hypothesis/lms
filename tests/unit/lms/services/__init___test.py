import pytest

from lms.services import includeme
from lms.services.application_instance_getter import ApplicationInstanceGetter
from lms.services.canvas_api import CanvasAPIClient
from lms.services.group_info import GroupInfoService
from lms.services.h_api import HAPI
from lms.services.launch_verifier import LaunchVerifier
from lms.services.lis_result_sourcedid import LISResultSourcedIdService
from lms.services.lti_h import LTIHService
from lms.services.lti_outcomes import LTIOutcomesClient


class TestIncludeme:
    @pytest.mark.parametrize(
        "name,service_class",
        (
            ("ai_getter", ApplicationInstanceGetter),
            ("canvas_api_client", CanvasAPIClient),
            ("h_api", HAPI),
            ("launch_verifier", LaunchVerifier),
            ("lis_result_sourcedid", LISResultSourcedIdService),
            ("lti_outcomes_client", LTIOutcomesClient),
            ("group_info", GroupInfoService),
            ("lti_h", LTIHService),
        ),
    )
    def test_it_has_the_expected_service(self, name, service_class, pyramid_config):
        includeme(pyramid_config)

        assert pyramid_config.find_service_factory(name=name) == service_class
