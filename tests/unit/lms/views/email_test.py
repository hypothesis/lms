from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPFound

from lms.services.exceptions import ExpiredJWTError, InvalidJWTError
from lms.views.email import unsubscribe, unsubscribed


def test_unsubscribe(pyramid_request, email_unsubscribe_service):
    pyramid_request.matchdict["token"] = sentinel.token

    result = unsubscribe(pyramid_request)

    email_unsubscribe_service.unsubscribe.assert_called_once_with(sentinel.token)
    assert isinstance(result, HTTPFound)
    assert result.location == "http://example.com/email/unsubscribed"


@pytest.mark.parametrize("exception", [ExpiredJWTError, InvalidJWTError])
def test_unsubscribe_error(pyramid_request, email_unsubscribe_service, exception):
    pyramid_request.matchdict["token"] = sentinel.token
    email_unsubscribe_service.unsubscribe.side_effect = exception

    result = unsubscribe(pyramid_request)

    assert result == {"message": "Something went wrong while unsubscribing."}


def test_unsubscribed(pyramid_request):
    assert unsubscribed(pyramid_request) == {"message": "You've been unsubscribed"}
