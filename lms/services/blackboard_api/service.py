import re

from lms.services.blackboard_api._schemas import (
    BlackboardListFilesSchema,
    BlackboardPublicURLSchema,
)
from lms.services.exceptions import BlackboardFileNotFoundInCourse, HTTPError
from lms.validation.authentication import OAuthTokenResponseSchema

#: A regex for parsing just the file_id part out of one of our custom
#: blackboard://content-resource/<file_id>/ URLs.
DOCUMENT_URL_REGEX = re.compile(
    r"blackboard:\/\/content-resource\/(?P<file_id>[^\/]*)\/"
)


class BlackboardAPIClient:
    def __init__(
        self,
        blackboard_host,
        client_id,
        client_secret,
        redirect_uri,
        http_service,
        oauth2_token_service,
    ):  # pylint:disable=too-many-arguments
        self.blackboard_host = blackboard_host
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        self._http_service = http_service
        self._oauth2_token_service = oauth2_token_service

    def get_token(self, authorization_code):
        """
        Get an access token from Blackboard and save it in the DB.

        :raise services.HTTPError: if something goes wrong with the access
            token request to Blackboard
        """
        # Send a request to Blackboard to get an access token.
        response = self._http_service.post(
            self._api_url("oauth2/token"),
            data={
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri,
                "code": authorization_code,
            },
            auth=(self.client_id, self.client_secret),
            schema=OAuthTokenResponseSchema,
        )

        # Save the access token to the DB.
        self._oauth2_token_service.save(
            response.validated_data["access_token"],
            response.validated_data.get("refresh_token"),
            response.validated_data.get("expires_in"),
        )

    def list_files(self, course_id):
        """
        Return the list of files in the given course.

        :raise ProxyAPIAccessTokenError: if we don't have a Blackboard API
            access token for the current user
        """
        return self._http_service.get(
            self._api_url(f"courses/uuid:{course_id}/resources"),
            oauth=True,
            schema=BlackboardListFilesSchema,
        ).validated_data

    def public_url(self, course_id, document_url):
        file_id = DOCUMENT_URL_REGEX.search(document_url)["file_id"]

        try:
            return self._http_service.get(
                self._api_url(f"courses/uuid:{course_id}/resources/{file_id}"),
                oauth=True,
                schema=BlackboardPublicURLSchema,
            ).validated_data
        except HTTPError as err:
            if err.response.status_code == 404:
                raise BlackboardFileNotFoundInCourse(file_id) from err
            raise

    def _api_url(self, path):
        """Return the full Blackboard API URL for the given path."""
        return f"https://{self.blackboard_host}/learn/api/public/v1/{path}"


def factory(_context, request):
    application_instance = request.find_service(name="application_instance").get()
    settings = request.registry.settings

    return BlackboardAPIClient(
        blackboard_host=application_instance.lms_host(),
        client_id=settings["blackboard_api_client_id"],
        client_secret=settings["blackboard_api_client_secret"],
        redirect_uri=request.route_url("blackboard_api.oauth.callback"),
        http_service=request.find_service(name="http"),
        oauth2_token_service=request.find_service(name="oauth2_token"),
    )
