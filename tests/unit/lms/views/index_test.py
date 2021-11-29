from lms.views.index import index


class TestIndexView:
    def test_it_does_nowt(self, pyramid_request):
        template_params = index(pyramid_request)

        assert not template_params
