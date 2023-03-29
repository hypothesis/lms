import pytest

from lms.resources import LTILaunchResource


@pytest.mark.usefixtures(
    "application_instance_service", "assignment_service", "course_service"
)
class TestLTILaunchResource:
    def test_application_instance(self, lti_launch, application_instance_service):
        assert (
            lti_launch.application_instance
            == application_instance_service.get_current.return_value
        )

    def test_js_config(self, pyramid_request, JSConfig):
        lti_launch = LTILaunchResource(pyramid_request)

        js_config = lti_launch.js_config

        JSConfig.assert_called_once_with(lti_launch, pyramid_request)
        assert js_config == JSConfig.return_value

    @pytest.fixture
    def lti_launch(self, pyramid_request):
        return LTILaunchResource(pyramid_request)

    @pytest.fixture(autouse=True)
    def JSConfig(self, patch):
        return patch("lms.resources.lti_launch.JSConfig")
