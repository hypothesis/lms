# -*- coding: utf-8 -*-

import pytest

from lms.util import generate_username
from lms.util import generate_provider
from lms.util import generate_provider_unique_id
from lms.util import MissingToolConsumerIntanceGUIDError
from lms.util import MissingUserIDError


class TestGenerateUsername:
    def test_it_returns_a_30_char_string(self):
        request_params = {
            "tool_consumer_instance_guid": "VCSy*G1u3:canvas-lms",
            "user_id": "4533***70d9",
        }

        username = generate_username(request_params)

        assert isinstance(username, str)
        assert len(username) == 30

    def test_it_raises_if_tool_consumer_instance_guid_is_missing(self):
        request_params = {"user_id": "4533***70d9"}

        with pytest.raises(MissingToolConsumerIntanceGUIDError):
            generate_username(request_params)

    def test_it_raises_if_user_id_is_missing(self):
        request_params = {"tool_consumer_instance_guid": "VCSy*G1u3:canvas-lms"}

        with pytest.raises(MissingUserIDError):
            generate_username(request_params)


class TestGenerateProvider:
    def test_it_just_returns_the_tool_consumer_instance_guid(self):
        request_params = {"tool_consumer_instance_guid": "VCSy*G1u3:canvas-lms"}

        provider_unique_id = generate_provider(request_params)

        assert provider_unique_id == "VCSy*G1u3:canvas-lms"

    @pytest.mark.parametrize(
        "request_params",
        [
            {},
            {"tool_consumer_instance_guid": ""},
            {"tool_consumer_instance_guid": None},
        ],
    )
    def test_it_raises_if_tool_consumer_instance_guid_is_missing(self, request_params):
        with pytest.raises(MissingToolConsumerIntanceGUIDError):
            generate_provider(request_params)


class TestGenerateProviderUniqueID:
    def test_it_just_returns_the_user_id(self):
        request_params = {"user_id": "4533***70d9"}

        provider_unique_id = generate_provider_unique_id(request_params)

        assert provider_unique_id == "4533***70d9"

    @pytest.mark.parametrize("request_params", [{}, {"user_id": ""}, {"user_id": None}])
    def test_it_raises_if_user_id_is_missing(self, request_params):
        with pytest.raises(MissingUserIDError):
            generate_provider_unique_id(request_params)
