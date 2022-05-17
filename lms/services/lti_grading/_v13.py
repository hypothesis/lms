from datetime import datetime, timezone
from urllib.parse import urlparse

from lms.services.exceptions import ExternalRequestError
from lms.services.lti_grading.interface import LTIGradingService
from lms.services.ltia_http import LTIAHTTPService


class LTI13GradingService(LTIGradingService):
    # See: LTI1.3 Assignment and Grade Services https://www.imsglobal.org/spec/lti-ags/v2p0

    LTIA_SCOPES = [
        "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
        "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
        "https://purl.imsglobal.org/spec/lti-ags/scope/score",
    ]

    def __init__(self, grading_url, ltia_service: LTIAHTTPService):
        super().__init__(grading_url)
        self._ltia_service = ltia_service

    def read_result(self, grading_id):
        try:
            response = self._ltia_service.request(
                "GET",
                self._service_url(self.grading_url, "/results"),
                scopes=self.LTIA_SCOPES,
                params={"user_id": grading_id},
                headers={"Accept": "application/vnd.ims.lis.v2.resultcontainer+json"},
            )
        except ExternalRequestError as err:
            if err.status_code == 404:
                return None
            raise

        results = response.json()
        if not results:
            return None

        try:
            return results[-1]["resultScore"] / results[-1]["resultMaximum"]
        except (ZeroDivisionError, KeyError, IndexError):
            return None

    def record_result(self, grading_id, score=None, canvas_extensions=None):
        """
        https://erau.instructure.com/doc/api/score.html#method.lti/ims/scores.create
        """
        payload = {
            "scoreMaximum": 1,
            "scoreGiven": score,
            "userId": grading_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "activityProgress": "Completed",
            "gradingProgress": "FullyGraded",
        }

        if canvas_extensions:
            payload["https://canvas.instructure.com/lti/submission"] = {
                "subission_type": "basic_lti_launch",
                "submission_data": canvas_extensions.lti_launch_url,
                "submitted_at": canvas_extensions.submitted_at
                or datetime(2001, 1, 1, tzinfo=timezone.utc),
            }

        return self._ltia_service.request(
            "POST",
            self._service_url(self.grading_url, "/scores"),
            scopes=self.LTIA_SCOPES,
            json=payload,
            headers={"Content-Type": "application/vnd.ims.lis.v1.score+json"},
        )

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
