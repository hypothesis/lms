"""A collection of fixtures for making signed launches."""

import random
import time

import oauthlib.common
import oauthlib.oauth1
import pytest

from tests import factories

__all__ = (
    "do_lti_launch",
    "oauth1_credentials",
    "application_instance",
    "oauth1_sign_data",
)


@pytest.fixture
def do_lti_launch(app, oauth1_sign_data):
    def do_lti_launch(url, form_data, sign=True, headers=None, **kwargs):
        if not headers:
            headers = {}

        if sign:
            form_data = oauth1_sign_data(url, form_data)

        return app.post(
            url,
            params=form_data,
            headers=dict(
                {
                    "Accept": "text/html",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                **headers,
            ),
            **kwargs,
        )

    return do_lti_launch


@pytest.fixture
def oauth1_credentials(application_instance):
    return {
        "consumer_key": application_instance.consumer_key,
        "shared_secret": application_instance.shared_secret,
    }


@pytest.fixture
def application_instance(db_session):  # pylint:disable=unused-argument
    return factories.ApplicationInstance(tool_consumer_instance_guid="GUID")


@pytest.fixture
def oauth1_sign_data(oauth1_credentials):
    def oauth1_sign_data(url, data):
        oauth_client = oauthlib.oauth1.Client(
            oauth1_credentials["consumer_key"], oauth1_credentials["shared_secret"]
        )

        data.update(
            {
                "oauth_consumer_key": oauth1_credentials["consumer_key"],
                "oauth_callback": "about:blank",
                "oauth_nonce": "".join(random.choices("0123456789abcdef", k=64)),
                "oauth_signature_method": "HMAC-SHA1",
                "oauth_timestamp": str(int(time.time())),
                "oauth_version": "1.0",
            }
        )

        data["oauth_signature"] = oauth_client.get_oauth_signature(
            oauthlib.common.Request(url, "POST", body=data)
        )

        return data

    return oauth1_sign_data
