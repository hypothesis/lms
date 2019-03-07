from unittest import mock

import pytest
from sqlalchemy.orm.exc import NoResultFound
from pylti.common import LTIException

from lms.util import get_application_instance
from lms.util import lti_launch
from lms.exceptions import MissingLTILaunchParamError
from lms.models import ApplicationInstance


class TestGetApplicationInstance:
    def test_it_returns_the_matching_application_instance(self, pyramid_request):
        application_instance = ApplicationInstance(
            consumer_key="TEST_OAUTH_CONSUMER_KEY"
        )
        pyramid_request.db.add(application_instance)

        assert (
            get_application_instance(pyramid_request.db, "TEST_OAUTH_CONSUMER_KEY")
            == application_instance
        )

    def test_it_crashes_if_theres_no_matching_application_instance(
        self, pyramid_request
    ):
        with pytest.raises(NoResultFound):
            get_application_instance(pyramid_request.db, "TEST_OAUTH_CONSUMER_KEY")

    @pytest.fixture(autouse=True)
    def application_instances(self, pyramid_request):
        """Some "noise" application instances."""
        # Add some "noise" application instances to the DB for every test, to
        # make the tests more realistic.
        application_instances = [
            ApplicationInstance(consumer_key="NOISE_1"),
            ApplicationInstance(consumer_key="NOISE_2"),
            ApplicationInstance(consumer_key="NOISE_3"),
        ]
        pyramid_request.db.add_all(application_instances)
        return application_instances


class TestLTILaunch:
    def test_it_raises_if_theres_no_oauth_consumer_key(self, pyramid_request, wrapper):
        del pyramid_request.params["oauth_consumer_key"]

        with pytest.raises(MissingLTILaunchParamError, match="oauth_consumer_key"):
            wrapper(pyramid_request)

    def test_it_crashes_if_theres_no_application_instance_in_the_db(
        self, pyramid_request, wrapper, ai_getter
    ):
        ai_getter.shared_secret.side_effect = ConsumerKeyError()

        with pytest.raises(ConsumerKeyError):
            wrapper(pyramid_request)

    def test_it_verifies_the_request(self, pyramid_request, pylti, wrapper):
        wrapper(pyramid_request)

        pylti.common.verify_request_common.assert_called_once_with(
            {"TEST_OAUTH_CONSUMER_KEY": {"secret": "TEST_SECRET"}},
            pyramid_request.url,
            pyramid_request.method,
            pyramid_request.headers,
            pyramid_request.params,
        )

    def test_it_crashes_if_verification_fails(self, pyramid_request, wrapper, pylti):
        pylti.common.verify_request_common.side_effect = LTIException(
            "TEST_ERROR_MESSAGE"
        )

        with pytest.raises(LTIException, match="TEST_ERROR_MESSAGE"):
            wrapper(pyramid_request)

    def test_it_builds_a_jwt(self, build_jwt_from_lti_launch, wrapper, pyramid_request):
        wrapper(pyramid_request)

        build_jwt_from_lti_launch.assert_called_once_with(
            pyramid_request.params, "test_secret"
        )

    def test_it_calls_the_wrapped_view(
        self, view, wrapper, pyramid_request, build_jwt_from_lti_launch
    ):
        wrapper(pyramid_request)

        view.assert_called_once_with(
            pyramid_request, build_jwt_from_lti_launch.return_value
        )

    @pytest.fixture
    def application_instance(self):
        """The matching ApplicationInstance from the DB."""
        return mock.create_autospec(
            ApplicationInstance,
            instance=True,
            spec_set=True,
            consumer_key="TEST_OAUTH_CONSUMER_KEY",
            shared_secret="TEST_SECRET",
        )

    @pytest.fixture
    def view(self):
        """The original view that's being wrapped."""
        return mock.create_autospec(lambda request, jwt_token: None)

    @pytest.fixture
    def wrapper(self, view):
        """The wrapped view."""
        return lti_launch(view)

    @pytest.fixture(autouse=True)
    def build_jwt_from_lti_launch(self, patch):
        return patch("lms.util._lti_launch.build_jwt_from_lti_launch")

    @pytest.fixture(autouse=True)
    def pylti(self, patch):
        return patch("lms.util._lti_launch.pylti")
