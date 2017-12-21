import requests
import pyramid.httpexceptions as exc
from lms.models.application_instance import find_by_oauth_consumer_key
from lms.models.tokens import find_token_by_user_id

GET = 'get'
POST = 'post'
GET_ALL = 'get_all'


class CanvasResponse:
    """Standardize output to handle pagination."""

    def __init__(self, status_code, result_json):
        """Store the status code and result json."""
        self.status_code = status_code
        self.result_json = result_json

    def json(self):
        """Return the json from the request."""
        return self.result_json


class CanvasApi:
    """Class to encapsulate interactions with the Canvas api."""

    def __init__(self, canvas_token, canvas_domain):
        """Initialize the canvas api with a domain and a token."""
        self.canvas_token = canvas_token
        self.canvas_domain = canvas_domain

    def proxy(self, endpoint_url, method, params):
        """Proxy a method to canvas."""
        response = None
        params['access_token'] = self.canvas_token
        url = f"{self.canvas_domain}{endpoint_url}"
        if method == GET:
            response = requests.get(url=url, params=params)
        elif method == POST:
            response = requests.post(url)
        elif method == GET_ALL:
            return self.get_all(endpoint_url, params)

        return CanvasResponse(response.status_code, response.json())

    def get_all(self, endpoint_url, params):
        params['per_page'] = 100
        params['page'] = 1
        resp_jsons = []
        url = f"{self.canvas_domain}{endpoint_url}"
        response = requests.get(url=url, params=params)
        resp_jsons.append(response.json())
        while 'rel="next"' in response.headers['link']:
            params['page'] = params['page'] + 1
            response = requests.get(url=url, params=params)
            resp_jsons.append(response.json())

        return CanvasResponse(200, [item for resp in resp_jsons for item in resp])


def canvas_api(view_function):
    """
    Decorate a route to include an instance of the CanvasApi class.

    Expects to be passed a user and decoded_jwt that includes at least:
    {
      # The consumer key belonging to the application instance
      # the jwt originiated from
      consumer_key
    }
    """
    def wrapper(request, decoded_jwt, user):
        """Wrap view function."""
        if user is None:
            return exc.HTTPNotFound()

        token = find_token_by_user_id(request.db, user.id)
        consumer_key = decoded_jwt['consumer_key']
        application_instance = find_by_oauth_consumer_key(request.db, consumer_key)

        if token is None or application_instance is None:
            return exc.HTTPNotFound()

        api = CanvasApi(
            token.access_token,
            application_instance.lms_url
        )
        return view_function(request, decoded_jwt, user=user,
                             canvas_api=api)
    return wrapper
