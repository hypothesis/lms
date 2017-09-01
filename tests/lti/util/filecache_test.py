# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from lti.util import filecache

import pytest


@pytest.mark.usefixtures('os_fixture')
class TestExistsHTML(object):

    def test_it_calls_isfile_with_the_correct_path(self, os_fixture, pyramid_request):
        filecache.exists_html(hash_='abc123', settings=pyramid_request.registry.settings)

        os_fixture.path.isfile.assert_called_once_with('/var/lib/lti/abc123.html')

    @pytest.mark.parametrize('isfile_return_value', [True, False])
    def test_it_returns_what_isfile_returns(self, os_fixture, isfile_return_value, pyramid_request):
        os_fixture.path.isfile.return_value = isfile_return_value

        assert filecache.exists_html(hash_='abc123', settings=pyramid_request.registry.settings) == isfile_return_value


@pytest.mark.usefixtures('os_fixture')
class TestExistsPDF(object):

    def test_it_calls_isfile_with_the_correct_path(self, os_fixture, pyramid_request):
        filecache.exists_pdf(hash_='abc123', settings=pyramid_request.registry.settings)

        os_fixture.path.isfile.assert_called_once_with('/var/lib/lti/abc123.pdf')

    @pytest.mark.parametrize('isfile_return_value', [True, False])
    def test_it_returns_what_isfile_returns(self, os_fixture, isfile_return_value, pyramid_request):
        os_fixture.path.isfile.return_value = isfile_return_value

        assert filecache.exists_pdf(hash_='abc123', settings=pyramid_request.registry.settings) == isfile_return_value


@pytest.fixture
def os_fixture(patch):
    return patch('lti.util.filecache.os')
