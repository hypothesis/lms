import datetime
import jwt

from unittest import mock
import pytest
from pyramid.httpexceptions import HTTPBadRequest

from lms.config import resources
from lms.models import CourseGroup


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
        assert claims["sub"] == "acct:75a0b8df844a493bc789385bbbd885@TEST_AUTHORITY"
        assert before <= claims["nbf"] <= after
        assert claims["exp"] > before

    def test_hypothesis_config_includes_the_group(
        self, lti_launch, models, pyramid_request
    ):
        group = models.CourseGroup.get.return_value

        groups = lti_launch.hypothesis_config["services"][0]["groups"]

        models.CourseGroup.get.assert_called_once_with(
            pyramid_request.db,
            mock.sentinel.tool_consumer_instance_guid,
            mock.sentinel.context_id,
        )
        assert groups == [group.pubid]

    def test_if_theres_no_tool_consumer_instance_guid(
        self, lti_launch, lti_params_for, models, pyramid_request
    ):
        del lti_params_for.return_value["tool_consumer_instance_guid"]

        groups = lti_launch.hypothesis_config["services"][0]["groups"]

        models.CourseGroup.get.assert_called_once_with(
            pyramid_request.db, None, mock.sentinel.context_id
        )
        assert groups == [models.CourseGroup.get.return_value.pubid]

    def test_if_theres_no_context_id(
        self, lti_launch, lti_params_for, models, pyramid_request
    ):
        del lti_params_for.return_value["context_id"]

        groups = lti_launch.hypothesis_config["services"][0]["groups"]

        models.CourseGroup.get.assert_called_once_with(
            pyramid_request.db, mock.sentinel.tool_consumer_instance_guid, None
        )
        assert groups == [models.CourseGroup.get.return_value.pubid]

    def test_if_theres_no_tool_consumer_instance_guid_OR_context_id(
        self, lti_launch, lti_params_for, models, pyramid_request
    ):
        del lti_params_for.return_value["tool_consumer_instance_guid"]
        del lti_params_for.return_value["context_id"]

        groups = lti_launch.hypothesis_config["services"][0]["groups"]

        models.CourseGroup.get.assert_called_once_with(pyramid_request.db, None, None)
        assert groups == [models.CourseGroup.get.return_value.pubid]

    def test_it_raises_AssertionError_if_theres_no_group(self, lti_launch, models):
        models.CourseGroup.get.return_value = None

        with pytest.raises(AssertionError, match="group should always exist by now"):
            lti_launch.hypothesis_config

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
            "tool_consumer_instance_guid": mock.sentinel.tool_consumer_instance_guid,
            "context_id": mock.sentinel.context_id,
            # A valid oauth_consumer_key (matches one for which the
            # provisioning features are enabled).
            "oauth_consumer_key": "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef",
        }
        return lti_params_for

    @pytest.fixture(autouse=True)
    def models(self, patch):
        models = patch("lms.config.resources.models")
        models.CourseGroup.get.return_value = mock.create_autospec(
            CourseGroup, instance=True, spec_set=True
        )
        return models

    @pytest.fixture(autouse=True)
    def util(self, patch):
        util = patch("lms.config.resources.util")
        util.generate_username.return_value = "75a0b8df844a493bc789385bbbd885"
        return util
