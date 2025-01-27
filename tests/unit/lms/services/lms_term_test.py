from datetime import datetime
from unittest.mock import sentinel

import pytest

from lms.services.lms_term import LMSTermService, factory


class TestLMSTermService:
    def test_get_term_not_enought_data(self, svc, pyramid_request):
        assert not svc.get_term(pyramid_request.lti_params)

    def test_get_term(self, svc, pyramid_request):
        term_starts = datetime(2020, 1, 1)
        term_ends = datetime(2020, 6, 1)
        term_name = "NICE TERM"
        lti_params = pyramid_request.lti_params
        lti_params["custom_term_start"] = term_starts.isoformat()
        lti_params["custom_term_end"] = term_ends.isoformat()
        lti_params["custom_term_name"] = term_name

        term = svc.get_term(pyramid_request.lti_params)

        assert term.starts_at == term_starts
        assert term.ends_at == term_ends
        assert term.name == term_name
        assert (
            term.tool_consumer_instance_guid
            == lti_params["tool_consumer_instance_guid"]
        )

    @pytest.mark.parametrize(
        "name,start,end,term_id,expected",
        [
            (
                "NICE TERM",
                "2020-01-01 00:00:00",
                "2020-06-01 00:00:00",
                None,
                "TEST_TOOL_CONSUMER_INSTANCE_GUID:NICE TERM:2020-01-01 00:00:00:2020-06-01 00:00:00",
            ),
            (
                "NICE TERM",
                None,
                "2020-06-01 00:00:00",
                None,
                "TEST_TOOL_CONSUMER_INSTANCE_GUID:NICE TERM:-:2020-06-01 00:00:00",
            ),
            (
                "NICE TERM",
                "2020-01-01 00:00:00",
                None,
                None,
                "TEST_TOOL_CONSUMER_INSTANCE_GUID:NICE TERM:2020-01-01 00:00:00:-",
            ),
            (
                "NICE TERM",
                "2020-01-01 00:00:00",
                "2020-06-01 00:00:00",
                "TERM_ID",
                "TEST_TOOL_CONSUMER_INSTANCE_GUID:TERM_ID",
            ),
        ],
    )
    def test_get_term_key(
        self, svc, pyramid_request, name, start, end, term_id, expected
    ):
        lti_params = pyramid_request.lti_params
        lti_params["custom_term_start"] = start
        lti_params["custom_term_end"] = end
        lti_params["custom_term_name"] = name
        lti_params["custom_term_id"] = term_id

        term = svc.get_term(pyramid_request.lti_params)

        assert term.key == expected

    @pytest.fixture()
    def svc(self, pyramid_request):
        return LMSTermService(db=pyramid_request.db)


class TestFactory:
    def test_it(self, pyramid_request, LMSTermService):
        service = factory(sentinel.context, pyramid_request)

        LMSTermService.assert_called_once_with(db=pyramid_request.db)
        assert service == LMSTermService.return_value

    @pytest.fixture
    def LMSTermService(self, patch):
        return patch("lms.services.lms_term.LMSTermService")
