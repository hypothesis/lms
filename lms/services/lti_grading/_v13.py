from datetime import datetime, timezone

from lms.services import LTIAHTTPService
from lms.services.exceptions import ExternalRequestError
from lms.services.lti_grading._interface import LTIGradingClient


class LTI13GradingClient(LTIGradingClient):
    LTIA_SCOPES = [
        "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
        "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
        "https://purl.imsglobal.org/spec/lti-ags/scope/score",
    ]

    def __init__(self, grading_url, ltia_service: LTIAHTTPService):
        self.grading_url = grading_url
        self.ltia_service = ltia_service

    def read_result(self, user_id):
        try:
            response = self.ltia_service.request(
                self.LTIA_SCOPES,
                "GET",
                self.grading_url + "/results",
                params={"user_id": user_id},
                headers={"Accept": "application/vnd.ims.lis.v2.resultcontainer+json"},
            )
        except ExternalRequestError as err:
            if err.status_code == 404:
                return None
            raise

        results = response.json()
        if not results:
            return None

        return results[-1]["resultScore"] / results[-1]["resultMaximum"]

    def record_result(self, user_id, score=None, pre_record_hook=None):
        return self.ltia_service.request(
            self.LTIA_SCOPES,
            "POST",
            self.grading_url + "/scores",
            json={
                "scoreMaximum": 1,
                "scoreGiven": score,
                "userId": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "activityProgress": "Completed",
                "gradingProgress": "FullyGraded",
            },
            headers={"Content-Type": "application/vnd.ims.lis.v2.lineitem+json"},
        )
