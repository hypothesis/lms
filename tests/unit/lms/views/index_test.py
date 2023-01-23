from h_matchers import Any
from pyramid.httpexceptions import HTTPFound

from lms.views.index import index


class TestIndexView:
    def test_it(self, pyramid_request):
        response = index(pyramid_request)

        assert response == Any.instance_of(HTTPFound)
