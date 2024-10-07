from datetime import datetime
from unittest.mock import Mock, sentinel

import pytest
from freezegun import freeze_time
from h_matchers import Any
from pytest import param

from lms.product.family import Family
from lms.services.exceptions import ExternalRequestError, StudentNotInCourse
from lms.services.lti_grading._v13 import LTI13GradingService
from tests import factories


class TestLTI13GradingService:
    @freeze_time("2022-04-04")
    def test_read_lti_result(self, svc, response, ltia_http_service, lti_registration):
        ltia_http_service.request.return_value.json.return_value = response
        svc.line_item_url = "https://lms.com/lineitems?param=1"

        result = svc.read_result(sentinel.user_id)

        ltia_http_service.request.assert_called_once_with(
            lti_registration,
            "GET",
            "https://lms.com/lineitems/results?param=1",
            scopes=svc.LTIA_SCOPES,
            params={"user_id": sentinel.user_id},
            headers={"Accept": "application/vnd.ims.lis.v2.resultcontainer+json"},
        )
        assert (
            result.score == response[-1]["resultScore"] / response[-1]["resultMaximum"]
        )

    def test_read_lti_result_empty(self, svc, ltia_http_service):
        ltia_http_service.request.side_effect = ExternalRequestError(
            response=Mock(status_code=404)
        )

        result = svc.read_result(sentinel.user_id)

        assert not result.score
        assert not result.comment

    def test_read_lti_result_raises(self, svc, ltia_http_service):
        ltia_http_service.request.side_effect = ExternalRequestError(
            response=Mock(status_code=500)
        )

        with pytest.raises(ExternalRequestError):
            svc.read_result(sentinel.user_id)

    def test_read_empty_lti_result(self, svc, ltia_http_service):
        ltia_http_service.request.return_value.json.return_value = []

        result = svc.read_result(sentinel.user_id)

        assert not result.score
        assert not result.comment

    @pytest.mark.parametrize(
        "bad_response",
        (
            param([{"resultScore": None, "resultMaximum": 100}], id="TypeError"),
            param([{"resultScore": 1, "resultMaximum": 0}], id="ZeroDivisionError"),
            param([{"resultScore": 1}], id="KeyError (max)"),
            param([{"resultMaximum": 10}], id="KeyError (score)"),
        ),
    )
    def test_read_bad_response_lti_result(self, svc, ltia_http_service, bad_response):
        ltia_http_service.request.return_value.json.return_value = bad_response

        result = svc.read_result(sentinel.user_id)

        assert not result.score
        assert not result.comment

    def test_read_result_blackboard(
        self,
        blackboard_svc,
        ltia_http_service,
        blackboard_response,
        misc_plugin,
        lti_registration,
    ):
        ltia_http_service.request.return_value = Mock(links={"next": None})
        ltia_http_service.request.return_value.json.return_value = blackboard_response
        blackboard_svc.line_item_url = "https://lms.com/lineitems?param=1"

        result = blackboard_svc.read_result(sentinel.user_id)

        ltia_http_service.request.assert_called_once_with(
            lti_registration,
            "GET",
            "https://lms.com/lineitems/results?param=1",
            scopes=blackboard_svc.LTIA_SCOPES,
            params={"limit": 1000},
            headers={"Accept": "application/vnd.ims.lis.v2.resultcontainer+json"},
        )
        assert (
            result.score
            == blackboard_response[0]["resultScore"]
            / blackboard_response[0]["resultMaximum"]
        )
        misc_plugin.clean_lms_grading_comment.assert_called_once_with(
            blackboard_response[0]["comment"]
        )
        assert result.comment == misc_plugin.clean_lms_grading_comment.return_value

    def test_read_result_blackboard_pagination_limit(
        self, blackboard_svc, ltia_http_service, blackboard_response, caplog
    ):
        ltia_http_service.request.return_value = Mock(links={"next": sentinel.next})
        ltia_http_service.request.return_value.json.return_value = blackboard_response

        result = blackboard_svc.read_result(sentinel.user_id)

        assert "paginated" in caplog.text
        assert result

    def test_get_score_maximum(self, svc, ltia_http_service, lti_registration):
        ltia_http_service.request.return_value.json.return_value = [
            {"scoreMaximum": sentinel.score_max, "id": svc.line_item_url},
            {"scoreMaximum": 1, "id": sentinel.other_lineitem},
        ]

        score = svc.get_score_maximum(sentinel.resource_link_id)

        ltia_http_service.request.assert_called_once_with(
            lti_registration,
            "GET",
            "http://example.com/lineitems",
            scopes=svc.LTIA_SCOPES,
            params={"resource_link_id": sentinel.resource_link_id},
            headers={"Accept": "application/vnd.ims.lis.v2.lineitemcontainer+json"},
        )
        assert score == sentinel.score_max

    def test_get_score_maximum_with_error(self, svc, ltia_http_service):
        ltia_http_service.request.side_effect = ExternalRequestError(
            response=Mock(status_code=500)
        )

        assert svc.get_score_maximum(sentinel.resource_link_id) is None

    def test_get_score_maximum_no_line_item(self, svc, ltia_http_service):
        ltia_http_service.request.return_value.json.return_value = [
            {"scoreMaximum": sentinel.score_max, "id": sentinel.other_lineitem}
        ]

        assert not svc.get_score_maximum(sentinel.resource_link_id)

    @pytest.mark.parametrize("is_canvas", [True, False])
    def test_sync_grade(
        self,
        svc,
        ltia_http_service,
        lti_v13_application_instance,
        is_canvas,
        assignment,
    ):
        lms_user = factories.LMSUser(lti_v13_user_id=sentinel.user_id)
        if is_canvas:
            lti_v13_application_instance.lti_registration.issuer = (
                "https://canvas.instructure.com"
            )

        response = svc.sync_grade(
            lti_v13_application_instance,
            assignment,
            datetime(2022, 4, 4).isoformat(),
            lms_user,
            sentinel.grade,
        )

        payload = {
            "scoreMaximum": 1,
            "scoreGiven": sentinel.grade,
            "userId": sentinel.user_id,
            "timestamp": "2022-04-04T00:00:00",
            "activityProgress": "Completed",
            "gradingProgress": "FullyGraded",
        }
        if is_canvas:
            payload["https://canvas.instructure.com/lti/submission"] = {
                "new_submission": False
            }

        ltia_http_service.request.assert_called_once_with(
            lti_v13_application_instance.lti_registration,
            "POST",
            "LIS_OUTCOME_SERVICE_URL/scores",
            scopes=svc.LTIA_SCOPES,
            json=payload,
            headers={"Content-Type": "application/vnd.ims.lis.v1.score+json"},
        )
        assert response == ltia_http_service.request.return_value

    @freeze_time("2022-04-04")
    @pytest.mark.parametrize("comment", [sentinel.comment, None])
    def test_record_result(
        self, svc, ltia_http_service, comment, misc_plugin, lti_registration
    ):
        svc.line_item_url = "https://lms.com/lineitems?param=1"

        response = svc.record_result(sentinel.user_id, sentinel.score, comment=comment)

        payload = {
            "scoreMaximum": 1,
            "scoreGiven": sentinel.score,
            "userId": sentinel.user_id,
            "timestamp": "2022-04-04T00:00:00+00:00",
            "activityProgress": "Completed",
            "gradingProgress": "FullyGraded",
        }
        if comment:
            misc_plugin.format_grading_comment_for_lms.assert_called_once_with(comment)
            payload["comment"] = misc_plugin.format_grading_comment_for_lms.return_value

        ltia_http_service.request.assert_called_once_with(
            lti_registration,
            "POST",
            "https://lms.com/lineitems/scores?param=1",
            scopes=svc.LTIA_SCOPES,
            json=payload,
            headers={"Content-Type": "application/vnd.ims.lis.v1.score+json"},
        )
        assert response == ltia_http_service.request.return_value

    def test_record_result_raises_ExternalRequestError(self, svc, ltia_http_service):
        ltia_http_service.request.side_effect = ExternalRequestError(
            response=Mock(status_code=500)
        )

        with pytest.raises(ExternalRequestError):
            svc.record_result(sentinel.user_id, sentinel.score)

    @pytest.mark.parametrize(
        "code,text",
        [
            (400, "User could not be found:"),
            (403, "User in requested score is not enrolled in the org unit"),
            (404, "User in requested score does not exist"),
        ],
    )
    def test_record_result_raises_StudentNotInCourse(
        self, svc, ltia_http_service, code, text
    ):
        ltia_http_service.request.side_effect = ExternalRequestError(
            response=Mock(status_code=code, text=text)
        )

        with pytest.raises(StudentNotInCourse):
            svc.record_result(sentinel.user_id, sentinel.score)

    def test_create_line_item(self, svc, ltia_http_service, lti_registration):
        response = svc.create_line_item(
            sentinel.resource_link_id,
            sentinel.label,
            sentinel.score_maximum,
        )

        ltia_http_service.request.assert_called_once_with(
            lti_registration,
            "POST",
            svc.line_item_container_url,
            scopes=svc.LTIA_SCOPES,
            json={
                "scoreMaximum": sentinel.score_maximum,
                "label": sentinel.label,
                "resourceLinkId": sentinel.resource_link_id,
            },
            headers={"Content-Type": "application/vnd.ims.lis.v2.lineitem+json"},
        )
        assert response == ltia_http_service.request.return_value.json.return_value

    def test_record_result_calls_hook(self, svc, ltia_http_service, lti_registration):
        my_hook = Mock(return_value={"my_dict": 1})

        svc.record_result(sentinel.user_id, score=1.5, pre_record_hook=my_hook)

        my_hook.assert_called_once_with(request_body=Any.dict(), score=1.5)
        ltia_http_service.request.assert_called_once_with(
            lti_registration,
            "POST",
            "http://example.com/lineitem/scores",
            scopes=svc.LTIA_SCOPES,
            json={"my_dict": 1},
            headers={"Content-Type": "application/vnd.ims.lis.v1.score+json"},
        )

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
    def blackboard_response(self):
        return [
            {
                "id": "https://lms.example.com/context/2923/lineitems/1/results/5323497",
                "scoreOf": "https://lms.example.com/context/2923/lineitems/1",
                "userId": sentinel.user_id,
                "resultScore": 0.83,
                "resultMaximum": 1,
                "comment": "This is exceptional work.",
            },
            {
                "id": "https://lms.example.com/context/2923/lineitems/1/results/5323497",
                "scoreOf": "https://lms.example.com/context/2923/lineitems/1",
                "userId": "ANOTHER_USERID",
                "resultScore": 0.0,
                "resultMaximum": 1,
                "comment": "This is exceptional work.",
            },
        ]

    @pytest.fixture
    def svc(self, ltia_http_service, misc_plugin, lti_registration):
        return LTI13GradingService(
            "http://example.com/lineitem",
            "http://example.com/lineitems",
            ltia_http_service,
            product_family=Family.CANVAS,
            misc_plugin=misc_plugin,
            lti_registration=lti_registration,
        )

    @pytest.fixture
    def assignment(self):
        return factories.Assignment(lis_outcome_service_url="LIS_OUTCOME_SERVICE_URL")

    @pytest.fixture
    def blackboard_svc(self, ltia_http_service, misc_plugin, lti_registration):
        return LTI13GradingService(
            "http://example.com/lineitem",
            "http://example.com/lineitems",
            ltia_http_service,
            product_family=Family.BLACKBOARD,
            misc_plugin=misc_plugin,
            lti_registration=lti_registration,
        )
