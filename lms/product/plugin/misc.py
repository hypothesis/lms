import json
from typing import TYPE_CHECKING, NotRequired, TypedDict

from pyramid.request import Request

from lms.js_config_types import AutoGradingConfig
from lms.models import ApplicationInstance, Assignment, LTIParams
from lms.services.html_service import strip_html_tags

if TYPE_CHECKING:
    from lms.models import LTIRegistration


class AssignmentConfig(TypedDict):
    document_url: str | None
    group_set_id: str | None
    auto_grading_config: NotRequired[AutoGradingConfig | None]


class DeepLinkingPromptForGradableMixin:
    def deep_linking_prompt_for_gradable(
        self, application_instance: ApplicationInstance
    ) -> bool:
        """
        Whether or not to ask if the new assignment should be gradable.

        We'll only prompt for gradable assignments if the
        `HYPOTHESIS_PROMPT_FOR_GRADABLE` setting is enabled and we are in LTI1.3
        """
        if application_instance.lti_version == "LTI-1p0":
            return False

        ai_settings = application_instance.settings
        return ai_settings.get_setting(
            ai_settings.fields[ai_settings.Settings.HYPOTHESIS_PROMPT_FOR_GRADABLE]
        )


class MiscPlugin:
    """
    Plugin for product differences that don't have a better abstractions yet.

    Works as a placeholder location to centralize LMS differences here without
    the need to create bigger abstractions before it's clear what that
    abstraction should look like.

    The aim also includes to remove any checks around `product.family` around
    the code base.

    New methods here should not try to get a very tight API as easier to
    refactor once multiple LMSes have the same issue vs getting the right
    parameters in the first occurrence.

    Once any of these is implemented by more than one product or a group of
    methods looks like it could belong to their own plugin it's time to
    refactor them out.
    """

    # Whether or not to prompt for an assignment title while deep linking.
    deep_linking_prompt_for_title = True

    def deep_linking_prompt_for_gradable(self, _application_instance) -> bool:
        """Whether or not to ask if the new assignment should be gradable."""
        return False

    def post_launch_assignment_hook(
        self, request, js_config, assignment
    ):  # pragma: nocover
        """Run any actions needed for a successful launch of an assignment."""

    def accept_grading_comments(self, application_instance):
        """Whether to accept comments while grading."""
        # This is a LTI 1.3 only feature
        return application_instance.lti_version == "1.3.0"

    def clean_lms_grading_comment(self, comment: str) -> str:
        """Clean a comment coming from the LMS to display it in our grading comment textarea."""
        return strip_html_tags(comment)

    def format_grading_comment_for_lms(self, comment: str) -> str:
        """Format grading comment before sending it over via the API."""
        return comment

    def is_assignment_gradable(self, lti_params: LTIParams) -> bool:
        """Check if the assignment of the current launch is gradable."""
        return bool(lti_params.get("lis_outcome_service_url"))

    def get_ltia_aud_claim(self, lti_registration: "LTIRegistration") -> str:
        """Get the value of the `aud` claim used in LTI advantage requests."""
        return lti_registration.token_url

    def get_assignment_configuration(
        self,
        request: Request,
        assignment: Assignment | None,
        historical_assignment: Assignment | None,
    ) -> AssignmentConfig:
        if assignment:
            return self._assignment_config_from_assignment(assignment)

        if historical_assignment:
            return self._assignment_config_from_assignment(historical_assignment)

        # For LMSes that support both DL and non-DL assignments fallback to the DL parameters
        deep_linked_config = self.get_deep_linked_assignment_configuration(request)
        return self._assignment_config_from_deep_linked_config(deep_linked_config)

    def get_deeplinking_launch_url(self, request, _assignment_configuration: dict):
        """
        Launch URL for deep linked assignments.

        To which URL to point the deep linked assignments in the LMS.
        This URL wel'll be part of the deep link response message
        to finish the configuration during a deep link request.
        """
        # In general we'll point to our regular basic launch URL.
        # The assignment configuration we'll be retrieved by other methods (eg, custom parameters) so that parameter is not used here.
        return request.route_url("lti_launches")

    def get_deep_linked_assignment_configuration(self, request) -> dict:
        """Get the configuration of an assignment present in the current launch deep link."""
        params = {}
        possible_parameters = [
            "url",
            "group_set",
            "deep_linking_uuid",
            "auto_grading_config",
        ]

        for param in possible_parameters:
            # Get the value from the custom parameters set during deep linking
            if value := request.lti_params.get(f"custom_{param}"):
                params[param] = value

        return params

    def is_speed_grader_launch(self, _request) -> bool:  # pragma: nocover
        # SpeedGrader is a Canvas only concept
        return False

    @staticmethod
    def _assignment_config_from_assignment(assignment: Assignment) -> AssignmentConfig:
        """Get the configuration of an assignment from our DB."""
        config = AssignmentConfig(
            document_url=assignment.document_url,
            group_set_id=assignment.extra.get("group_set_id"),
        )
        if auto_grading_config := assignment.auto_grading_config:
            config["auto_grading_config"] = auto_grading_config.asdict()

        return config

    @staticmethod
    def _assignment_config_from_deep_linked_config(
        deep_linked_config: dict,
    ) -> AssignmentConfig:
        """Get the configuration of an assignment based on the Deep linked configuration."""
        config = AssignmentConfig(
            document_url=deep_linked_config.get("url"),
            group_set_id=deep_linked_config.get("group_set"),
        )

        if auto_grading_config := deep_linked_config.get("auto_grading_config"):
            config["auto_grading_config"] = json.loads(auto_grading_config)

        return config
