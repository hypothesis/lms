import logging

from lms.views.helpers import log_retries_callback


def test_log_retries_callback(pyramid_request, caplog):
    caplog.set_level(logging.DEBUG)
    pyramid_request.headers["Retry-Count"] = "1"

    log_retries_callback(pyramid_request)

    assert "succeeded after 1 retries" in "".join(caplog.messages)


def test_log_retries_callback_doesnt_log_not_retry(pyramid_request, caplog):
    caplog.set_level(logging.DEBUG)

    log_retries_callback(pyramid_request)

    assert not caplog.messages
