import requests


class BlackboardAPIClient:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        self._session = requests.Session()

    def get_token(self, authorization_code):
        request = requests.Request(
            "POST",
            "https://blackboard.hypothes.is/learn/api/public/v1/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri,
                "code": authorization_code,
            },
            auth=(self.client_id, self.client_secret),
        ).prepare()

        try:
            response = self._session.send(request, timeout=9)
            response.raise_for_status()
        except requests.RequestException as err:
            raise

        access_token = response.json()["access_token"]

        def do(url):
            return requests.get(
                url, headers={"Authorization": f"Bearer {access_token}"},
            )

        print(
            do(
                "https://blackboard.hypothes.is/learn/api/public/v1/courses/_5_1/resources"
            ).json()["results"][1]["downloadUrl"]
        )

    def _validated_response(self, request, schema, request_depth=1):
        """
        Send a Canvas API request and validate and return the response.

        If a validation schema is given then the parsed and validated response
        params will be available on the returned response object as
        `response.parsed_params` (a dict).

        :param request: a prepared request to some Canvas API endpoint
        :param schema: The schema class to validate the contents of the response
            with.
        :param request_depth: The number of requests made so far for pagination
        """

        try:
            response = self._session.send(request, timeout=9)
            response.raise_for_status()
        except RequestException as err:
            CanvasAPIError.raise_from(err)

        result = None
        try:
            result = schema(response).parse()
        except ValidationError as err:
            CanvasAPIError.raise_from(err)

        # Handle pagination links. See:
        # https://canvas.instructure.com/doc/api/file.pagination.html
        next_url = response.links.get("next")
        if next_url:
            # We can only append results if the response is expecting multiple
            # items from the Canvas API
            if not schema.many:
                CanvasAPIError.raise_from(
                    TypeError(
                        "Canvas returned paginated results but we expected a single"
                        " value"
                    )
                )

            # Don't make requests forever
            if request_depth < self.PAGINATION_MAXIMUM_REQUESTS:
                request.url = next_url["url"]
                result.extend(
                    self._validated_response(
                        request, schema, request_depth=request_depth + 1
                    )
                )

        return result


def blackboard_api_client_service_factory(context, request):
    client_secret = request.registry.settings.get("blackboard_client_secret")
    return BlackboardAPIClient(
        client_id="8baa49c0-fb04-4404-acca-7b9bb51405e0",
        client_secret=client_secret,
        redirect_uri=request.route_url("blackboard_oauth_callback"),
    )
