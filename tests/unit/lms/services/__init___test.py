from unittest import mock

from lms.services import includeme
from lms.services.application_instance_getter import ApplicationInstanceGetter
from lms.services.canvas_api import CanvasAPIClient
from lms.services.group_info_upsert import GroupInfoUpsert
from lms.services.h_api import HAPI
from lms.services.launch_verifier import LaunchVerifier
from lms.services.lis_result_sourcedid import LISResultSourcedIdService
from lms.services.lti_h import LTIHService
from lms.services.lti_outcomes import LTIOutcomesClient


def test_includeme(pyramid_config):
    includeme(pyramid_config)

    assert (
        pyramid_config.find_service_factory(name="ai_getter")
        == ApplicationInstanceGetter
    )
    assert (
        pyramid_config.find_service_factory(name="canvas_api_client") == CanvasAPIClient
    )
    assert pyramid_config.find_service_factory(name="h_api") == HAPI
    assert pyramid_config.find_service_factory(name="launch_verifier") == LaunchVerifier
    assert (
        pyramid_config.find_service_factory(name="lis_result_sourcedid")
        == LISResultSourcedIdService
    )
    assert (
        pyramid_config.find_service_factory(name="lti_outcomes_client")
        == LTIOutcomesClient
    )
    assert (
        pyramid_config.find_service_factory(name="group_info_upsert") == GroupInfoUpsert
    )
    assert pyramid_config.find_service_factory(name="lti_h") == LTIHService
