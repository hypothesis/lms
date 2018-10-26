"""Set up reporting of exceptions to Sentry."""

import sentry_sdk
from sentry_sdk.integrations.pyramid import PyramidIntegration


def includeme(_config):
    sentry_sdk.init(integrations=[PyramidIntegration()])
