import re
import time

import oauthlib.common
import oauthlib.oauth1
import pytest
from h_matchers import Any
from httpretty import httpretty

from lms.models import ApplicationInstance, ModuleItemConfiguration
from tests.functional.base_class import TestBaseClass


class TestBasicLTILaunch(TestBaseClass):
    SHARED_SECRET = "TEST_SECRET"
    OAUTH_CONSUMER_KEY = "Hypothesis1b40eafba184a131307049e01e9c147d"
    OAUTH_NONCE = "38d6db30e395417659d068164ca95169"
    OAUTH_CLIENT = oauthlib.oauth1.Client(OAUTH_CONSUMER_KEY, SHARED_SECRET)

    @pytest.mark.usefixtures("http_intercept")
    def test_a_good_request_loads_fine(self, app, lti_params):
        result = self.lti_launch(app, lti_params, status=200)

        self.assert_response_is_html(result)

    # ---------------------------------------------------------------------- #
    # Assertions

    @classmethod
    def assert_response_is_html(cls, response):
        assert response.headers["Content-Type"] == Any.string.matching("^text/html")
        assert response.html

    # ---------------------------------------------------------------------- #
    # Helper methods

    @classmethod
    def lti_launch(cls, app, params, status=200):
        url = "/lti_launches"

        params = cls.oauth_sign_params(url, params)

        return app.post(
            url,
            params=params,
            headers={
                "Accept": "text/html",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            status=status,
        )

    @classmethod
    def oauth_sign_params(cls, url, params):
        params.update(
            {
                "oauth_consumer_key": cls.OAUTH_CONSUMER_KEY,
                "oauth_nonce": cls.OAUTH_NONCE,
                "oauth_timestamp": str(int(time.time())),
            }
        )
        params["oauth_signature"] = cls.OAUTH_CLIENT.get_oauth_signature(
            oauthlib.common.Request(f"http://localhost{url}", "POST", body=params)
        )

        return params

    # Fixtures ------------------------------------------------------------- #

    @pytest.fixture(autouse=True)
    def application_instance(self, db_session, app):
        # Load app so we create the instance after the DB has been truncated

        application_instance = ApplicationInstance(
            consumer_key=self.OAUTH_CONSUMER_KEY,
            shared_secret=self.SHARED_SECRET,
            lms_url="test_lms_url",
            requesters_email="test_requesters_email",
        )

        db_session.add(application_instance)
        db_session.commit()

        return application_instance

    @pytest.fixture(autouse=True, params=["configured", "unconfigured"])
    def module_item_configuration(self, request, db_session, application_instance):
        if request.param == "unconfigured":
            return

        module_item_configuration = ModuleItemConfiguration(
            resource_link_id="rli-1234",
            tool_consumer_instance_guid="IMS Testing",
            document_url="http://example.com",
        )

        db_session.add(module_item_configuration)
        db_session.commit()

        return module_item_configuration

    @pytest.fixture
    def lti_params(self):
        return self.json_fixture("lti_params/good_params.json")

    @pytest.yield_fixture
    def http_intercept(self, _http_intercept):
        """
        Monkey-patch Python's socket core module to mock all HTTP responses.

        We will catch calls to H's API and return 200. All other calls will
        raise an exception, allowing to you see who are are trying to call.
        """
        # We only need to reset once per tests, all other setup can be done
        # once in `_http_intercept()`
        yield
        httpretty.reset()

    @pytest.yield_fixture(scope="session")
    def _http_intercept(self):
        # Mock all calls to the H API
        httpretty.register_uri(
            method=Any(),
            uri=re.compile(r"^https://example.com/private/api/.*"),
            body="",
        )

        # Catch URLs we aren't expecting or have failed to mock
        def error_response(request, uri, response_headers):
            raise NotImplementedError(f"Unexpected call to URL: {request.method} {uri}")

        httpretty.register_uri(method=Any(), uri=re.compile(".*"), body=error_response)

        httpretty.enable()
        yield
        httpretty.disable()
