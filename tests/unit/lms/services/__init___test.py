import pytest

from lms.services import (
    application_instance,
    assignment,
    blackboard_api,
    canvas_api,
    course,
    grading_info,
    grant_token,
    group_info,
    h_api,
    http,
    includeme,
    launch_verifier,
    lti_h,
    lti_outcomes,
    oauth1,
    oauth2_token,
    vitalsource,
)


class TestIncludeme:
    @pytest.mark.parametrize(
        "iface,factory",
        (
            (
                application_instance.ApplicationInstanceService,
                application_instance.factory,
            ),
            (assignment.AssignmentService, assignment.factory),
            (blackboard_api.BlackboardAPIClient, blackboard_api.factory),
            (canvas_api.CanvasAPIClient, canvas_api.canvas_api_client_factory),
            (course.CourseService, course.course_service_factory),
            (grading_info.GradingInfoService, grading_info.GradingInfoService),
            (grant_token.GrantTokenService, grant_token.factory),
            (group_info.GroupInfoService, group_info.GroupInfoService),
            (h_api.HAPI, h_api.HAPI),
            (http.HTTPService, http.factory),
            (launch_verifier.LaunchVerifier, launch_verifier.LaunchVerifier),
            (lti_h.LTIHService, lti_h.LTIHService),
            (lti_outcomes.LTIOutcomesClient, lti_outcomes.LTIOutcomesClient),
            (oauth1.OAuth1Service, oauth1.OAuth1Service),
            (
                oauth2_token.OAuth2TokenService,
                oauth2_token.oauth2_token_service_factory,
            ),
            (vitalsource.VitalSourceService, vitalsource.factory),
        ),
    )
    def test_it_has_the_expected_service(self, iface, factory, pyramid_config):
        includeme(pyramid_config)

        assert pyramid_config.find_service_factory(iface) == factory
