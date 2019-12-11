# https://docs.moodle.org/dev/Creating_a_web_service_client

import requests

from lms.tool_consumer.moodle.exception import MoodleException
from lms.tool_consumer.moodle.params import MoodleParams


class MoodleWebServiceClient:
    params = MoodleParams

    def __init__(self, base_url, ws_token):
        self.base_url = base_url
        self.ws_token = ws_token
        self.children = {}

    def call(self, area, function, params=None):
        url = self.base_url + "/webservice/rest/server.php"

        params.update(
            {
                "wstoken": self.ws_token,
                "wsfunction": area + "_" + function,
                "moodlewsrestformat": "json",
            }
        )
        params = self.params.flatten(params)

        response = requests.post(url, data=params)

        return self._handle_response(response)

    def _handle_response(self, response, error_class=MoodleException):
        data = response.json()

        if "exception" in data:
            raise error_class.from_dict(data)

        return data
