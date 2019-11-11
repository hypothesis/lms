import time

import oauthlib.common
import oauthlib.oauth1
import pytest

from lms.models import ApplicationInstance
from tests.functional.base_class import TestBaseClass


class TestLTICertification(TestBaseClass):
    SHARED_SECRET = "TEST_SECRET"
    OAUTH_CONSUMER_KEY = "Hypothesis1b40eafba184a131307049e01e9c147d"
    OAUTH_NONCE = "38d6db30e395417659d068164ca95169"
    OAUTH_CLIENT = oauthlib.oauth1.Client(OAUTH_CONSUMER_KEY, SHARED_SECRET)

    def test_a_good_request_loads_fine(self, app):
        result = self.lti_launch(app, status=200)

        params = self._get_lti_params()

        # Check a random parameter to see it's passed to the body
        assert "tool_consumer_instance_guid" in result.text
        assert params["tool_consumer_instance_guid"] in result.text

    # ---------------------------------------------------------------------- #
    # Helper methods

    def lti_launch(self, app, remove=None, status=200, **extras):
        url = "/lti_launches"
        params = self._get_lti_params(remove=remove, **extras)
        params = self._oauth_sign_params(url, params)

        return app.post(url, params=params, status=status)

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

    def _get_lti_params(self, remove=None, **extras):
        params = self.json_fixture("lti_certification/all_params_v1.1.json")

        for key in remove or []:
            params.pop(key)

        params.update(extras)

        return params

    @classmethod
    def _oauth_sign_params(cls, url, params):
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
