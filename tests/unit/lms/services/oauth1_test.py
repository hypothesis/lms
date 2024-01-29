import json
from unittest import mock

import pytest
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
                                    "text": "This is an example of an LTI launch link set via the Content-Item launch message.  Please launch it to pass the related certification test.",
                                    "icon": {
                                        "@id": "https://apps.imsglobal.org//lti/cert/images/icon.png",
                                        "height": 50,
                                        "width": 50,
                                    },
                                    "placementAdvice": {
                                        "displayHeight": 400,
                                        "displayWidth": 400,
                                        "presentationDocumentTarget": "IFRAME",
                                    },
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
                                    "custom": {
                                        "imscert": "launchbHYnJGxZ",
                                        "contextHistory": "$Context.id.history",
                                        "resourceHistory": "$ResourceLink.id.history",
                                        "dueDate": "$ResourceLink.submission.endDateTime",
                                        "userName": "$User.username",
                                        "userEmail": "$Person.email.primary",
                                        "userSysRoles": "@X@user.role@X@",
                                        "source": "link",
                                    },
                                },
                            ],
                        },
                        separators=(",", ":"),
                    ),
                },
                "http://photos.example.net/photos",
                "GET",
                "7cZohgSjlkbH8mR1mwIh6+4BM80=",
            ),
            # Blackboard
            (
                "",
                "",
                "9d9764e4-7920-4d78-9ee9-4a2ca8188ec4",
                1706518363,
                {
                    "content_items": '{"@context":"http://purl.imsglobal.org/ctx/lti/v1/ContentItem","@graph":[{"mediaType":"application/vnd.ims.lti.v1.ltilink","@type":"LtiLinkItem","url":"http://localhost/lti","title":"Sample LTI launch","text":"This is an example of an LTI launch link set via the Content-Item launch message.  Please launch it to pass the related certification test.","icon":{"@id" :"https://apps.imsglobal.org//lti/cert/images/icon.png","height":50,"width":50},"placementAdvice":{"displayHeight":400,"displayWidth":400,"presentationDocumentTarget":"IFRAME"},"lineItem":{"@type":"LineItem","label":"Chapter 13 quiz","reportingMethod":"res:totalScore","assignedActivity":{"@id":"http://toolprovider.example.com/assessment/66400","activityId":"a-9334df-33"},"scoreConstraints":{"@type":"NumericLimits","normalMaximum":100,"extraCreditMaximum":10,"totalMaximum":110}},"custom":{"imscert":"launch»bHYnJGxZ","contextHistory":"$Context.id.history","resourceHistory":"$ResourceLink.id.history","dueDate":"$ResourceLink.submission.endDateTime","userName":"$User.username","userEmail":"$Person.email.primary","userSysRoles":"@X@user.role@X@","source":"link"}}]}',
                    "data": "_19_1::_27_1::-1::true::false::_299_1::3b1b99704eca4f72b759484388f03fa7::false::false",
                    "lti_message_type": "ContentItemSelection",
                    "lti_version": "LTI-1p0",
                    "oauth_callback": "about:blank",
                },
                "https://aunltd-test.blackboard.com/webapps/blackboard/controller/lti/contentitem",
                "POST",
                "a5G1Lwe9gdLe3yiyYbTlRzYQMas=",
            ),
        ],
    )
    def test_sign(
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
        assert result["oauth_timestamp"] == timestamp
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
    def OAuth1(self, patch):
        return patch("lms.services.oauth1.OAuth1")
