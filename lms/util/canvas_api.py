import requests


GET = 'get'
POST = 'post'


class CanvasApi:

    def __init__(self, canvas_token, canvas_domain):
        self.canvas_token = canvas_token
        self.canvas_domain = canvas_domain


    def proxy(self, endpoint_url, method, params):
        response = None
        params['access_token'] = self.canvas_token
        url = f"{self.canvas_domain}{endpoint_url}"
        if method == GET:
            response = requests.get(url = url, params = params)
        elif method == POST:
            response = requests.post(url)

        return response


    def get_canvas_course_files(self, course_id, params):
        return self.proxy(f'/api/v1/courses/{course_id}/files', GET, params)
