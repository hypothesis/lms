from lms.views.canvas_proxy import canvas_proxy


class TestCanvasProxy(object):
    def test_it_rejects_request_with_bad_jwt(self, canvas_api_proxy_request):
        canvas_api_proxy_request.headers['Authorization'] = 'asdf'
        response = canvas_proxy(canvas_api_proxy_request)
        assert response.code_code == 401

    def test_it_accepts_request_with_good_jwt(self, canvas_api_proxy_request):
        response = canvas_proxy(canvas_api_proxy_request)
        assert response.code_code == 200

