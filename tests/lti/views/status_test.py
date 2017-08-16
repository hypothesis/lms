# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

import lti.views.status as views


@pytest.mark.usefixtures('db')
class TestStatus(object):
    def test_it_returns_okay_on_success(self, pyramid_request):
        result = views.status(pyramid_request)
        assert result == {'status': 'okay'}

    def test_it_fails_when_database_unreachable(self, pyramid_request, db):
        db.execute.side_effect = Exception('explode!')

        result = views.status(pyramid_request)
        assert result == {'status': 'failure',
                          'reason': 'Database connection failed'}

    @pytest.fixture
    def db(self, pyramid_request):
        db = mock.Mock()
        pyramid_request.db = db
        return db
