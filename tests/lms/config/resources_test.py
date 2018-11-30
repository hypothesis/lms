import datetime
import jwt

from unittest import mock
import pytest
from pyramid.httpexceptions import HTTPBadRequest

from lms.config import resources


class TestLTILaunch:
    def test_it_raises_if_no_lti_params_for_request(
        self, pyramid_request, lti_params_for
    ):
        lti_params_for.side_effect = HTTPBadRequest()

        with pytest.raises(HTTPBadRequest):
            resources.LTILaunch(pyramid_request)

    @pytest.mark.parametrize(
        "request_params,expected_display_name",
        [
            # It returns the full name if there is one.
            (
                {
                    "lis_person_name_full": "Test Full",
                    # Add given and family names too. These should be ignored.
                    "lis_person_name_given": "Test Given",
                    "lis_person_name_family": "Test Family",
                },
                "Test Full",
            ),
            # It strips leading and trailing whitespace from the full name.
            ({"lis_person_name_full": " Test Full  "}, "Test Full"),
            # If theres no full name it concatenates given and family names.
            (
                {
                    "lis_person_name_given": "Test Given",
                    "lis_person_name_family": "Test Family",
                },
                "Test Given Test Family",
            ),
            # If full name is empty it concatenates given and family names.
            (
                {
                    "lis_person_name_full": "",
                    "lis_person_name_given": "Test Given",
                    "lis_person_name_family": "Test Family",
                },
                "Test Given Test Family",
            ),
            (
                {
                    "lis_person_name_full": "   ",
                    "lis_person_name_given": "Test Given",
                    "lis_person_name_family": "Test Family",
                },
                "Test Given Test Family",
            ),
            # It strips leading and trailing whitespace from the concatenated
            # given name and family name.
            (
                {
                    "lis_person_name_given": "  Test Given  ",
                    "lis_person_name_family": "  Test Family  ",
                },
                "Test Given Test Family",
            ),
            # If theres no full name or given name it uses just the family name.
            ({"lis_person_name_family": "Test Family"}, "Test Family"),
            (
                {
                    "lis_person_name_full": "   ",
                    "lis_person_name_given": "",
                    "lis_person_name_family": "Test Family",
                },
                "Test Family",
            ),
            # It strips leading and trailing whitespace from just the family name.
            ({"lis_person_name_family": "  Test Family "}, "Test Family"),
            # If theres no full name or family name it uses just the given name.
            ({"lis_person_name_given": "Test Given"}, "Test Given"),
            (
                {
                    "lis_person_name_full": "   ",
                    "lis_person_name_given": "Test Given",
                    "lis_person_name_family": "",
                },
                "Test Given",
            ),
            # It strips leading and trailing whitespace from just the given name.
            ({"lis_person_name_given": "  Test Given "}, "Test Given"),
            # If there's nothing else it just returns "Anonymous".
            ({}, "Anonymous"),
            (
                {
                    "lis_person_name_full": "   ",
                    "lis_person_name_given": " ",
                    "lis_person_name_family": "",
                },
                "Anonymous",
            ),
            # If the full name is more than 30 characters long it truncates it.
            (
                {"lis_person_name_full": "Test Very Very Looong Full Name"},
                "Test Very Very Looong Full Na…",
            ),
            # If the given name is more than 30 characters long it truncates it.
            (
                {"lis_person_name_given": "Test Very Very Looong Given Name"},
                "Test Very Very Looong Given N…",
            ),
            # If the family name is more than 30 characters long it truncates it.
            (
                {"lis_person_name_family": "Test Very Very Looong Family Name"},
                "Test Very Very Looong Family…",
            ),
            # If the concatenated given name + family name is more than 30
            # characters long it truncates it.
            (
                {
                    "lis_person_name_given": "Test Very Very",
                    "lis_person_name_family": "Looong Concatenated Name",
                },
                "Test Very Very Looong Concate…",
            ),
        ],
    )
    def test_h_display_name(
        self, request_params, expected_display_name, lti_params_for, pyramid_request
    ):
        lti_params_for.return_value = request_params

        assert (
            resources.LTILaunch(pyramid_request).h_display_name == expected_display_name
        )

    def test_h_groupid_raises_if_theres_no_tool_consumer_instance_guid(
        self, lti_params_for, pyramid_request
    ):
        lti_params_for.return_value = {}
        with pytest.raises(
            HTTPBadRequest,
            match='Required parameter "tool_consumer_instance_guid" missing from LTI params',
        ):
            resources.LTILaunch(pyramid_request).h_groupid

    def test_h_groupid_raises_if_theres_no_context_id(
        self, lti_params_for, pyramid_request
    ):
        lti_params_for.return_value = {"tool_consumer_instance_guid": "test_guid"}
        with pytest.raises(
            HTTPBadRequest,
            match='Required parameter "context_id" missing from LTI params',
        ):
            resources.LTILaunch(pyramid_request).h_groupid

    def test_h_groupid(self, lti_launch):
        assert (
            lti_launch.h_groupid
            == "group:d55a3c86dd79d390ec8dc6a8096d0943044ea268@TEST_AUTHORITY"
        )

    def test_h_group_name_raises_if_theres_no_context_title(self, lti_launch):
        with pytest.raises(HTTPBadRequest):
            lti_launch.h_group_name

    @pytest.mark.parametrize(
        "context_title,expected_group_name",
        (
            ("Test Course", "Test Course"),
            (" Test Course", "Test Course"),
            ("Test Course ", "Test Course"),
            (" Test Course ", "Test Course"),
            ("Test   Course", "Test   Course"),
            ("Object Oriented Programming 101", "Object Oriented Programm…"),
            ("Object Oriented Polymorphism 101", "Object Oriented Polymorp…"),
            ("  Object Oriented Polymorphism 101  ", "Object Oriented Polymorp…"),
        ),
    )
    def test_h_group_name_returns_group_names_based_on_context_titles(
        self, context_title, expected_group_name, lti_params_for, pyramid_request
    ):
        lti_params_for.return_value = {"context_title": context_title}

        assert resources.LTILaunch(pyramid_request).h_group_name == expected_group_name

    def test_h_provider_just_returns_the_tool_consumer_instance_guid(
        self, lti_params_for, pyramid_request
    ):
        lti_params_for.return_value = {
            "tool_consumer_instance_guid": "VCSy*G1u3:canvas-lms"
        }

        provider = resources.LTILaunch(pyramid_request).h_provider

        assert provider == "VCSy*G1u3:canvas-lms"

    @pytest.mark.parametrize(
        "request_params",
        [
            {},
            {"tool_consumer_instance_guid": ""},
            {"tool_consumer_instance_guid": None},
        ],
    )
    def test_h_provider_raises_if_tool_consumer_instance_guid_is_missing(
        self, request_params, lti_params_for, pyramid_request
    ):
        lti_params_for.return_value = request_params

        with pytest.raises(
            HTTPBadRequest,
            match='Required parameter "tool_consumer_instance_guid" missing from LTI params',
        ):
            resources.LTILaunch(pyramid_request).h_provider

    def test_h_provider_unique_id_just_returns_the_user_id(
        self, lti_params_for, pyramid_request
    ):
        lti_params_for.return_value = {"user_id": "4533***70d9"}

        provider_unique_id = resources.LTILaunch(pyramid_request).h_provider_unique_id

        assert provider_unique_id == "4533***70d9"

    @pytest.mark.parametrize("request_params", [{}, {"user_id": ""}, {"user_id": None}])
    def test_h_provider_unique_id_raises_if_user_id_is_missing(
        self, request_params, lti_params_for, pyramid_request
    ):
        lti_params_for.return_value = request_params

        with pytest.raises(
            HTTPBadRequest, match='Required parameter "user_id" missing from LTI params'
        ):
            resources.LTILaunch(pyramid_request).h_provider_unique_id

    def test_h_username_returns_a_30_char_string(self, pyramid_request, lti_params_for):
        lti_params_for.return_value = {
            "tool_consumer_instance_guid": "VCSy*G1u3:canvas-lms",
            "user_id": "4533***70d9",
        }

        username = resources.LTILaunch(pyramid_request).h_username

        assert isinstance(username, str)
        assert len(username) == 30

    def test_h_username_raises_if_tool_consumer_instance_guid_is_missing(
        self, lti_params_for, pyramid_request
    ):
        lti_params_for.return_value = {"user_id": "4533***70d9"}

        with pytest.raises(
            HTTPBadRequest,
            match='Required parameter "tool_consumer_instance_guid" missing from LTI params',
        ):
            resources.LTILaunch(pyramid_request).h_username

    def test_h_username_raises_if_user_id_is_missing(
        self, lti_params_for, pyramid_request
    ):
        lti_params_for.return_value = {
            "tool_consumer_instance_guid": "VCSy*G1u3:canvas-lms"
        }

        with pytest.raises(
            HTTPBadRequest, match='Required parameter "user_id" missing from LTI params'
        ):
            resources.LTILaunch(pyramid_request).h_username

    def test_h_userid(self, pyramid_request, lti_params_for):
        lti_params_for.return_value = {
            "tool_consumer_instance_guid": "VCSy*G1u3:canvas-lms",
            "user_id": "4533***70d9",
        }

        userid = resources.LTILaunch(pyramid_request).h_userid

        assert userid == "acct:2569ad7b99f316ecc7dfee5c0c801c@TEST_AUTHORITY"

    def test_h_userid_raises_if_tool_consumer_instance_guid_is_missing(
        self, lti_params_for, pyramid_request
    ):
        lti_params_for.return_value = {"user_id": "4533***70d9"}

        with pytest.raises(
            HTTPBadRequest,
            match='Required parameter "tool_consumer_instance_guid" missing from LTI params',
        ):
            resources.LTILaunch(pyramid_request).h_userid

    def test_h_userid_raises_if_user_id_is_missing(
        self, lti_params_for, pyramid_request
    ):
        lti_params_for.return_value = {
            "tool_consumer_instance_guid": "VCSy*G1u3:canvas-lms"
        }

        with pytest.raises(
            HTTPBadRequest, match='Required parameter "user_id" missing from LTI params'
        ):
            resources.LTILaunch(pyramid_request).h_userid

    def test_hypothesis_config_raises_if_theres_no_oauth_consumer_key(
        self, lti_params_for, pyramid_request
    ):
        lti_params_for.return_value = {}

        with pytest.raises(
            HTTPBadRequest,
            match='Required parameter "oauth_consumer_key" missing from LTI params',
        ):
            resources.LTILaunch(pyramid_request).hypothesis_config

    def test_hypothesis_config_raises_if_theres_no_tool_consumer_instance_guid(
        self, lti_params_for, pyramid_request
    ):
        lti_params_for.return_value = {
            "oauth_consumer_key": "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef"
        }

        with pytest.raises(
            HTTPBadRequest,
            match='Required parameter "tool_consumer_instance_guid" missing from LTI params',
        ):
            resources.LTILaunch(pyramid_request).hypothesis_config

    def test_hypothesis_config_contains_one_service_config(self, lti_launch):
        assert len(lti_launch.hypothesis_config["services"]) == 1

    def test_hypothesis_config_includes_the_api_url(self, lti_launch):
        assert (
            lti_launch.hypothesis_config["services"][0]["apiUrl"]
            == "https://example.com/api/"
        )

    def test_hypothesis_config_includes_the_authority(self, lti_launch):
        assert (
            lti_launch.hypothesis_config["services"][0]["authority"] == "TEST_AUTHORITY"
        )

    def test_hypothesis_config_disables_share_links(self, lti_launch):
        assert lti_launch.hypothesis_config["services"][0]["enableShareLinks"] is False

    def test_hypothesis_config_includes_grant_token(self, lti_launch):
        before = int(datetime.datetime.now().timestamp())

        grant_token = lti_launch.hypothesis_config["services"][0]["grantToken"]

        claims = jwt.decode(
            grant_token,
            algorithms=["HS256"],
            key="TEST_JWT_CLIENT_SECRET",
            audience="example.com",
        )
        after = int(datetime.datetime.now().timestamp())
        assert claims["iss"] == "TEST_JWT_CLIENT_ID"
        assert claims["sub"] == "acct:16aa3b3e92cdfa53e5996d138a7013@TEST_AUTHORITY"
        assert before <= claims["nbf"] <= after
        assert claims["exp"] > before

    def test_hypothesis_config_includes_the_group(self, lti_launch, pyramid_request):
        groups = lti_launch.hypothesis_config["services"][0]["groups"]

        assert groups == [
            "group:d55a3c86dd79d390ec8dc6a8096d0943044ea268@TEST_AUTHORITY"
        ]

    def test_hypothesis_config_is_empty_if_provisioning_feature_is_disabled(
        self, pyramid_request, lti_launch, lti_params_for
    ):
        lti_params_for.return_value.update({"oauth_consumer_key": "some_other_key"})
        assert lti_launch.hypothesis_config == {}

    def test_rpc_server_config(self, lti_launch):
        assert lti_launch.rpc_server_config == {
            "allowedOrigins": ["http://localhost:5000"]
        }

    @pytest.fixture
    def lti_launch(self, pyramid_request):
        return resources.LTILaunch(pyramid_request)

    @pytest.fixture(autouse=True)
    def lti_params_for(self, patch):
        lti_params_for = patch("lms.config.resources.lti_params_for")
        lti_params_for.return_value = {
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
            "context_id": "test_context_id",
            "user_id": "test_user_id",
            # A valid oauth_consumer_key (matches one for which the
            # provisioning features are enabled).
            "oauth_consumer_key": "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef",
        }
        return lti_params_for
