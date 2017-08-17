import os

if 'STATSD_HOST' in os.environ:
    statsd_host = '{host}:{port}'.format(
        host=os.environ['STATSD_HOST'],
        port=os.environ.get('STATSD_PORT', '8125'))

    statsd_prefix = os.environ.get('STATSD_PREFIX', '')
