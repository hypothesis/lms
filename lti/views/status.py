# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging

from pyramid.view import view_config


log = logging.getLogger(__name__)


@view_config(route_name='status',
             renderer='json')
def status(request):
    try:
        request.db.execute('SELECT 1')
        return {'status': 'okay'}
    except Exception as exc:  # pylint:disable=broad-except
        log.exception(exc)
        return {'status': 'failure', 'reason': 'Database connection failed'}
