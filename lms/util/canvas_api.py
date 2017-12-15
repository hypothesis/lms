import requests
import pyramid.httpexceptions as exc
from lms.models.application_instance import find_by_oauth_consumer_key
from lms.models.tokens import find_token_by_user_id

GET = 'get'
POST = 'post'


class CanvasApi:

    def __init__(self, canvas_token, canvas_domain):
        """Initialize the canvas api with a domain and a token."""
        self.canvas_token = canvas_token
        self.canvas_domain = canvas_domain

    def proxy(self, endpoint_url, method, params):
        response = None
        params['access_token'] = self.canvas_token
        url = f"{self.canvas_domain}{endpoint_url}"
        if method == GET:
            response = requests.get(url=url, params=params)
        elif method == POST:
            response = requests.post(url)

        return response

    def get_canvas_course_files(self, course_id, params):
        return self.proxy(f'/api/v1/courses/{course_id}/files', GET, params)

def canvas_api(view_function):
    def wrapper(request, decoded_jwt, user):
        if user is None:
            return exc.HTTPNotFound()

        token = find_token_by_user_id(request.db, user.id)
        consumer_key = decoded_jwt['consumer_key']
        application_instance = find_by_oauth_consumer_key(request.db, consumer_key)

        if token is None or application_instance is None: 
            return exc.HTTPNotFound()

        canvas_api = CanvasApi(
            token.access_token,
            application_instance.lms_url
        )
        return view_function(request, decoded_jwt, user=user,
                canvas_api=canvas_api)
    return wrapper
