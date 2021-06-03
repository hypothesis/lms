from lms.services.application_instance import ApplicationInstanceService
from lms.services.http import HTTPService
from lms.services.oauth2_token import OAuth2TokenService
from lms.validation.authentication import OAuthTokenResponseSchema


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
            f"https://{self.blackboard_host}/learn/api/public/v1/oauth2/token",
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


def factory(_context, request):
    application_instance = request.find_service(ApplicationInstanceService).get()
    settings = request.registry.settings

    return BlackboardAPIClient(
        blackboard_host=application_instance.lms_host(),
        client_id=settings["blackboard_api_client_id"],
        client_secret=settings["blackboard_api_client_secret"],
        redirect_uri=request.route_url("blackboard_api.oauth.callback"),
        http_service=request.find_service(HTTPService),
        oauth2_token_service=request.find_service(OAuth2TokenService),
    )
