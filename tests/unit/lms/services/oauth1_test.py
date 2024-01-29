import hashlib
import json
from unittest import mock

import pytest
from h_matchers import Any
from requests import Request

from lms.services.oauth1 import OAuth1Service

pytestmark = pytest.mark.usefixtures("application_instance_service")


class TestOAuth1Service:
    def test_we_configure_OAuth1_correctly(self, service, OAuth1, application_instance):
        service.get_client()

        OAuth1.assert_called_once_with(
            client_key=application_instance.consumer_key,
            client_secret=application_instance.shared_secret,
            signature_method="HMAC-SHA1",
            signature_type="auth_header",
            force_include_body=True,
        )

    def test_we_can_be_used_to_sign_a_request(self, service, application_instance):
        request = Request(
            "POST",
            url="http://example.com",
            data={"param": "value"},
            auth=service.get_client(),
        )

        prepared_request = request.prepare()

        auth_header = prepared_request.headers["Authorization"].decode("iso-8859-1")

        assert auth_header.startswith("OAuth")
        assert 'oauth_version="1.0"' in auth_header
        assert (
            f'oauth_consumer_key="{application_instance.consumer_key}"' in auth_header
        )
        assert 'oauth_signature_method="HMAC-SHA1"' in auth_header

        # This currently doesn't verify the signature, it only checks that
        # one is present.
        assert "oauth_signature=" in auth_header

    def test_sign(
        self, service, signature, uuid, datetime, application_instance, hmac, base64
    ):
        datetime.now.return_value.timestamp.return_value = 10000

        payload = {
            "oauth_version": "1.0",
            "oauth_nonce": uuid.uuid4.return_value.hex,
            "oauth_timestamp": "10000",
            "oauth_consumer_key": application_instance.consumer_key,
            "oauth_signature_method": "HMAC-SHA1",
            "KEY": "VALUE",
        }

        signed_payload = service.sign("URL", "POST", {"KEY": "VALUE"})

        signature.collect_parameters.assert_called_once_with(
            body=Any.dict.containing(payload),
            exclude_oauth_signature=False,
            with_realm=False,
        )
        signature.normalize_parameters.assert_called_once_with(
            signature.collect_parameters.return_value
        )
        signature.signature_base_string.assert_called_once_with(
            "POST", "URL", signature.normalize_parameters.return_value
        )

        hmac.new.assert_called_once_with(
            (application_instance.shared_secret + "&").encode("utf-8"),
            signature.signature_base_string.return_value.encode.return_value,
            hashlib.sha1,
        )
        base64.b64encode.assert_called_once_with(
            hmac.new.return_value.digest.return_value
        )
        assert signed_payload == dict(
            payload, oauth_signature=base64.b64encode.return_value.decode.return_value
        )

    @pytest.mark.parametrize(
        "key,secret,nonce,timestamp,data,url,method,signature",
        [
            # https://lti.tools/oauth/
            (
                "dpf43f3p2l4k3l03",
                "kd94hf93k423kf44",
                "kllo9940pd9333jh",
                1191242096,
                {"size": "original", "file": "vacation.jpg"},
                "http://photos.example.net/photos",
                "GET",
                "Jg5MXVnexhzMDTv7IBUy3goIGqc=",
            ),
            # https://lti.tools/oauth/ with content items
            (
                "dpf43f3p2l4k3l03",
                "kd94hf93k423kf44",
                "kllo9940pd9333jh",
                1191242096,
                {
                    "content_items": json.dumps(
                        {
                            "@context": "http://purl.imsglobal.org/ctx/lti/v1/ContentItem",
                            "@graph": [
                                {
                                    "mediaType": "application/vnd.ims.lti.v1.ltilink",
                                    "@type": "LtiLinkItem",
                                    "url": "http://localhost/lti",
                                    "title": "Sample LTI launch",
                                    "lineItem": {
                                        "@type": "LineItem",
                                        "label": "Chapter 13 quiz",
                                        "reportingMethod": "res:totalScore",
                                        "assignedActivity": {
                                            "@id": "http://toolprovider.example.com/assessment/66400",
                                            "activityId": "a-9334df-33",
                                        },
                                        "scoreConstraints": {
                                            "@type": "NumericLimits",
                                            "normalMaximum": 100,
                                            "extraCreditMaximum": 10,
                                            "totalMaximum": 110,
                                        },
                                    },
                                },
                            ],
                        },
                        separators=(",", ":"),
                    ),
                },
                "http://photos.example.net/photos",
                "POST",
                "vtKTwm3wPH36s3fz20JH2fNjh8I=",
            ),
        ],
    )
    def test_sign_signature_value(
        self,
        service,
        uuid,
        datetime,
        application_instance,
        key,
        secret,
        nonce,
        timestamp,
        data,
        url,
        method,
        signature,
    ):
        application_instance.consumer_key = key
        application_instance.shared_secret = secret

        uuid.uuid4.return_value.hex = nonce
        datetime.now.return_value.timestamp.return_value = timestamp

        result = service.sign(url, method, data)

        assert result["oauth_signature_method"] == "HMAC-SHA1"
        assert result["oauth_nonce"] == nonce
        assert result["oauth_timestamp"] == str(timestamp)
        assert result["oauth_consumer_key"] == key
        assert result["oauth_signature"] == signature

    @pytest.fixture
    def service(self, context, pyramid_request):
        return OAuth1Service(context, pyramid_request)

    @pytest.fixture
    def context(self):
        # We don't use context, so it doesn't matter what it is
        return mock.sentinel.context

    @pytest.fixture
    def uuid(self, patch):
        return patch("lms.services.oauth1.uuid")

    @pytest.fixture
    def datetime(self, patch):
        return patch("lms.services.oauth1.datetime")

    @pytest.fixture
    def signature(self, patch):
        return patch("lms.services.oauth1.signature")

    @pytest.fixture
    def hmac(self, patch):
        return patch("lms.services.oauth1.hmac")

    @pytest.fixture
    def base64(self, patch):
        return patch("lms.services.oauth1.base64")

    @pytest.fixture
    def OAuth1(self, patch):
        return patch("lms.services.oauth1.OAuth1")
