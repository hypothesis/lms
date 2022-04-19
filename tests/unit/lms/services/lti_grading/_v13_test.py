from unittest.mock import Mock, sentinel

import pytest
from freezegun import freeze_time

from lms.services.exceptions import ExternalRequestError
from lms.services.lti_grading._v13 import LTI13GradingService


class TestLTI13GradingService:
    SERVICE_URL = "http://example.com/service_url"
    GRADING_ID = "lis_result_sourcedid"

    def test_read_lti_result(self, svc, response, ltia_http_service):
        ltia_http_service.request.return_value.json.return_value = response

        score = svc.read_result(self.GRADING_ID)

        ltia_http_service.request.assert_called_once_with(
            "GET",
            self.SERVICE_URL + "/results",
            scopes=svc.LTIA_SCOPES,
            params={"user_id": self.GRADING_ID},
            headers={"Accept": "application/vnd.ims.lis.v2.resultcontainer+json"},
        )
        assert score == response[-1]["resultScore"] / response[-1]["resultMaximum"]

    def test_read_lti_result_empty(self, svc, ltia_http_service):
        ltia_http_service.request.side_effect = ExternalRequestError(
            response=Mock(status_code=404)
        )

        score = svc.read_result(self.GRADING_ID)

        assert not score

    def test_read_lti_result_raises(self, svc, ltia_http_service):
        ltia_http_service.request.side_effect = ExternalRequestError(
            response=Mock(status_code=500)
        )

        with pytest.raises(ExternalRequestError):
            svc.read_result(self.GRADING_ID)

    def test_read_empty_lti_result(self, svc, ltia_http_service):
        ltia_http_service.request.return_value.json.return_value = []

        assert not svc.read_result(self.GRADING_ID)

    @pytest.mark.parameterize(
        "bad_response",
        (
            [{"resultScore": 1, "resultMaximum": 0}],
            [{"resultScore": 1}],
            [{"resultMaximum": 10}],
        ),
    )
    def test_read_bad_response_lti_result(self, svc, ltia_http_service, bad_response):
        ltia_http_service.request.return_value.json.return_value = bad_response

        assert not svc.read_result(self.GRADING_ID)

    @freeze_time("2022-04-04")
    def test_record_result(self, svc, ltia_http_service):
        response = svc.record_result(self.GRADING_ID, sentinel.score)

        ltia_http_service.request.assert_called_once_with(
            "POST",
            self.SERVICE_URL + "/scores",
            scopes=svc.LTIA_SCOPES,
            json={
                "scoreMaximum": 1,
                "scoreGiven": sentinel.score,
                "userId": self.GRADING_ID,
                "timestamp": "2022-04-04T00:00:00+00:00",
                "activityProgress": "Completed",
                "gradingProgress": "FullyGraded",
            },
            headers={"Content-Type": "application/vnd.ims.lis.v2.lineitem+json"},
        )
        assert response == ltia_http_service.request.return_value

    @pytest.fixture
    def response(self):
        return [
            {
                "id": "https://lms.example.com/context/2923/lineitems/1/results/5323497",
                "scoreOf": "https://lms.example.com/context/2923/lineitems/1",
                "userId": "5323497",
                "resultScore": 0.83,
                "resultMaximum": 1,
                "comment": "This is exceptional work.",
            }
        ]

    @pytest.fixture
    def svc(self, ltia_http_service):
        return LTI13GradingService(self.SERVICE_URL, ltia_http_service)
