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

    assert result == {
        "title": "Expired unsubscribe link",
        "message": """
                    <p>
                        It looks like the unsubscribe link that you clicked on was invalid or had expired.
                        Try clicking the unsubscribe link in a more recent email instead.
                    </p>
                    <p>
                        If the problem persists, you can
                         <a href="https://web.hypothes.is/get-help/?product=LMS_app" target="_blank" rel="noopener noreferrer">open a support ticket</a>
                         or visit our <a href="https://web.hypothes.is/help/" target="_blank" rel="noopener noreferrer">help documents</a>.
                    </p>
                    """,
    }


def test_unsubscribed(pyramid_request):
    assert unsubscribed(pyramid_request) == {"title": "You've been unsubscribed"}
