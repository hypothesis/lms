"""Set up reporting of exceptions to Sentry."""

import os

import sentry_sdk
import sentry_sdk.integrations.pyramid

from lms.sentry.helpers.before_send import before_send as _before_send


def includeme(_config):
    sentry_sdk.init(
        integrations=[sentry_sdk.integrations.pyramid.PyramidIntegration()],
        environment=os.environ.get("SENTRY_ENVIRONMENT"),
        send_default_pii=True,
        before_send=_before_send,
    )
