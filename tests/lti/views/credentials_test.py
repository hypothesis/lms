# -*- coding: utf-8 -*-

import json
import urllib
import pytest

from lti.views import credentials


class TestCredentials(object):

    def test_it_renders_empty_form_when_form_is_not_submitted(self, pyramid_request):
        pyramid_request.query_string = urllib.urlencode({
            'not_credentials_query_param': 'some_string',
        })

        returned = credentials.lti_credentials(pyramid_request)

        expected = {
            'form_submitted': False
        }

        assert returned == expected

    def test_it_renders_thank_you_message_when_form_is_submitted(self, pyramid_request):
        returned = credentials.lti_credentials(pyramid_request)
        expected = {
            'form_submitted': True,
            'key': 'key_a',
            'secret': 'secret_a',
            'host': 'host_a',
            'email': 'email_a'
        }
        assert returned == expected


@pytest.fixture
def pyramid_request(pyramid_request):
    data = {
        'key': 'key_a',
        'secret': 'secret_a',
        'host': 'host_a',
        'email': 'email_a',
    }

    pyramid_request.query_string = urllib.urlencode({
        'credentials': json.dumps(data)
    })

    return pyramid_request
