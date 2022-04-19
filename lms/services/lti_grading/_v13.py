from datetime import datetime, timezone

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
                self.grading_url + "/results",
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

    def record_result(self, grading_id, score=None):  # pylint:disable=arguments-differ
        return self._ltia_service.request(
            "POST",
            self.grading_url + "/scores",
            scopes=self.LTIA_SCOPES,
            json={
                "scoreMaximum": 1,
                "scoreGiven": score,
                "userId": grading_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "activityProgress": "Completed",
                "gradingProgress": "FullyGraded",
            },
            headers={"Content-Type": "application/vnd.ims.lis.v2.lineitem+json"},
        )
