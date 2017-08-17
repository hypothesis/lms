"""Report exceptions to Sentry."""

import os

import raven
from raven.utils.wsgi import get_environ


def get_raven_client(request):
    """Return the Raven client for reporting crashes to Sentry."""
    client = request.registry["raven.client"]
    client.http_context({
        'url': request.url,
        'method': request.method,
        'data': request.body,
        'query_string': request.query_string,
        'cookies': dict(request.cookies),
        'headers': dict(request.headers),
        'env': dict(get_environ(request.environ)),
    })
    client.user_context({
        'ip_address': request.client_addr,
    })
    request.add_finished_callback(lambda request: client.context.clear())
    return client


def includeme(config):
    environment = os.environ.get('ENV', 'dev')
    config.registry["raven.client"] = raven.Client(
        environment=environment,
        processors=[
            'raven.processors.SanitizePasswordsProcessor',
            'raven.processors.RemovePostDataProcessor',
        ],
    )
    config.add_request_method(get_raven_client, name="raven", reify=True)
