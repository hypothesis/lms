from unittest import mock

import pytest

from lms.resources import LTILaunchResource


@pytest.fixture(autouse=True)
def ModuleItemConfiguration(patch):
    return patch("lms.views.basic_lti_launch.ModuleItemConfiguration")


@pytest.fixture
def context():
    context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)
    context.js_config = {"urls": {}}
    return context


@pytest.fixture(autouse=True)
def via_url(patch):
    return patch("lms.views.basic_lti_launch.via_url")


@pytest.fixture
def lti_outcome_params():
    # Request params needed for calls to the LMS's Outcome Management service,
    # present when a student launches an assignment.
    #
    # These params are typically not present when a teacher launches an
    # assignment.
    return {
        "lis_result_sourcedid": "modelstudent-assignment1",
        "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
        "tool_consumer_info_product_family_code": "canvas",
        "context_id": "TEST_CONTEXT_ID",
        "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
    }
