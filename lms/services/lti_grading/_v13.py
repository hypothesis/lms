import logging
from datetime import UTC, datetime
from urllib.parse import urlparse

from lms.models import ApplicationInstance, Assignment, Family, LMSUser, LTIRegistration
from lms.product.plugin.misc import MiscPlugin
from lms.services.exceptions import ExternalRequestError, StudentNotInCourse
from lms.services.lti_grading.interface import GradingResult, LTIGradingService
from lms.services.ltia_http import LTIAHTTPService

LOG = logging.getLogger(__name__)


class LTI13GradingService(LTIGradingService):
    # See: LTI1.3 Assignment and Grade Services https://www.imsglobal.org/spec/lti-ags/v2p0

    LTIA_SCOPES = [  # noqa: RUF012
        "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
        # Although this is implied by scope/lineitem according to the spec
        # Moodle requires this one explicitly for the GET
        "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly",
        "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
        "https://purl.imsglobal.org/spec/lti-ags/scope/score",
    ]

    def __init__(  # noqa: PLR0913
        self,
        line_item_url,
        line_item_container_url,
        ltia_service: LTIAHTTPService,
        product_family: Family,
        misc_plugin: MiscPlugin,
        lti_registration: LTIRegistration,
    ):
        super().__init__(line_item_url, line_item_container_url)
        self._ltia_service = ltia_service
        self._product_family = product_family
        self._misc_plugin = misc_plugin
        self._lti_registration = lti_registration

    def read_result(self, grading_id) -> GradingResult:
        result = GradingResult(score=None, comment=None)

        params = {"user_id": grading_id}
        if self._product_family == Family.BLACKBOARD:
            # There's currently a bug in Blackboard's LTIA implementation.
            # Using the user filter in the request removes the comment field in the response's body.
            # So we'll remove the parameter and will search for the right student in the response.
            del params["user_id"]
            # We explicitly add a big limit parameter to try to fetch as many results as possible
            # without having to fetch more pages (which we have not implemented)
            params["limit"] = 1000

        try:
            response = self._ltia_service.request(
                self._lti_registration,
                "GET",
                self._service_url(self.line_item_url, "/results"),
                scopes=self.LTIA_SCOPES,
                params=params,
                headers={"Accept": "application/vnd.ims.lis.v2.resultcontainer+json"},
            )
        except ExternalRequestError as err:
            if err.status_code == 404:
                return result
            raise

        results = response.json()
        if self._product_family == Family.BLACKBOARD:
            # Due to the bug mentioned above we didn't use the API filtering by user for blackboard.
            # We'll filter ourselves here instead.
            results = [result for result in results if result["userId"] == grading_id]
            if response.links.get("next"):
                # We want to be notified if we are leaving results unfetched and likely start following these links
                LOG.error(
                    "Blackboard grading reading result, container with paginated results"
                )

        if not results:
            return result

        try:  # noqa: SIM105
            result.score = results[-1]["resultScore"] / results[-1]["resultMaximum"]
        except (TypeError, ZeroDivisionError, KeyError, IndexError):
            pass

        if comment := results[-1].get("comment"):
            result.comment = self._misc_plugin.clean_lms_grading_comment(comment)
        return result

    def get_score_maximum(self, resource_link_id) -> float | None:
        return self._read_grading_configuration(resource_link_id).get("scoreMaximum")

    def sync_grade(
        self,
        application_instance: ApplicationInstance,
        assignment: Assignment,
        grade_timestamp: str,
        lms_user: LMSUser,
        score: float,
    ):
        """
        Send a grade to the LMS.

        This is very similar to `record_result` but not scoped to the request context,
        taking all the necessary information as parameters.
        """
        assert lms_user.lti_v13_user_id, (  # noqa: S101
            "Trying to grade a student without lti_v13_user_id"
        )
        payload = LTI13GradingService._record_score_payload(
            score, lms_user.lti_v13_user_id, grade_timestamp
        )

        if application_instance.lti_registration.product_family == Family.CANVAS:
            # By default Canvas calls to /score create a new submission
            # Disable that behaviour and just submit the new grade.
            # See: https://canvas.instructure.com/doc/api/score.html
            payload["https://canvas.instructure.com/lti/submission"] = {
                "new_submission": False
            }
        return self._ltia_service.request(
            application_instance.lti_registration,
            "POST",
            self._service_url(assignment.lis_outcome_service_url, "/scores"),
            scopes=self.LTIA_SCOPES,
            json=payload,
            headers={"Content-Type": "application/vnd.ims.lis.v1.score+json"},
        )

    def record_result(self, grading_id, score=None, pre_record_hook=None, comment=None):
        payload = self._record_score_payload(
            score,
            grading_id,
            datetime.now(UTC).isoformat(),
        )
        if comment:
            payload["comment"] = self._misc_plugin.format_grading_comment_for_lms(
                comment
            )

        if pre_record_hook:
            payload = pre_record_hook(score=score, request_body=payload)

        try:
            return self._ltia_service.request(
                self._lti_registration,
                "POST",
                self._service_url(self.line_item_url, "/scores"),
                scopes=self.LTIA_SCOPES,
                json=payload,
                headers={"Content-Type": "application/vnd.ims.lis.v1.score+json"},
            )

        except ExternalRequestError as err:
            for expected_code, expected_text in [
                # Blackboard
                (400, "User could not be found:"),
                # D2L
                (403, "User in requested score is not enrolled in the org unit"),
                (404, "User in requested score does not exist"),
            ]:
                if (
                    err.status_code == expected_code
                    and expected_text in err.response.text
                ):
                    raise StudentNotInCourse(grading_id) from err

            raise

    def create_line_item(self, resource_link_id, label, score_maximum=100):
        """
        Create a new line item associated to one resource_link_id.

        https://www.imsglobal.org/spec/lti-ags/v2p0#container-request-filters

        :param resource_link_id: ID of the assignment this line item will
            belong to.
        :param label: Name for the new line item.
        :param score_maximum: Max score for the grades in the new line item.
        """
        payload = {
            "scoreMaximum": score_maximum,
            "label": label,
            "resourceLinkId": resource_link_id,
        }
        return self._ltia_service.request(
            self._lti_registration,
            "POST",
            self.line_item_container_url,
            scopes=self.LTIA_SCOPES,
            json=payload,
            headers={"Content-Type": "application/vnd.ims.lis.v2.lineitem+json"},
        ).json()

    def _read_grading_configuration(self, resource_link_id) -> dict:
        """
        Read the grading configuration of an assignment.

        In LTI nomenclature this is reading the line item container.
        :param resource_link_id: ID of the assignment on the LMS.
        """
        containers = []
        try:
            containers = self._ltia_service.request(
                self._lti_registration,
                "GET",
                self.line_item_container_url,
                scopes=self.LTIA_SCOPES,
                params={"resource_link_id": resource_link_id},
                headers={"Accept": "application/vnd.ims.lis.v2.lineitemcontainer+json"},
            ).json()

        except ExternalRequestError as err:
            LOG.info(
                "Error while reading grading config for %s. %s",
                resource_link_id,
                str(err),
            )

        # Only return the container relevant for the current launch
        for container in containers:
            if container["id"] == self.line_item_url:
                return container

        return {}

    @staticmethod
    def _record_score_payload(
        score: float | None, user_grading_id: str, timestamp: str
    ):
        return {
            "scoreMaximum": 1,
            "scoreGiven": score,
            "userId": user_grading_id,
            "timestamp": timestamp,
            "activityProgress": "Completed",
            "gradingProgress": "FullyGraded",
        }

    @staticmethod
    def _service_url(base_url, endpoint):
        """
        Build a complete URL for grading services.

        Some LMSs (eg Moodle) include query params on the service URL.
        Appending "/endpoint" naively will return an URL that it's not quite right:

            /lineitem?type=10/endpoint.

        Using urlparse here to build the URL correctly.
        """
        base = urlparse(base_url)
        return base._replace(path=base.path + endpoint).geturl()
