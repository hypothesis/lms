import re
from lms.validation.authentication import OAuthTokenResponseSchema


#: A regex for parsing just the file_id part out of one of our custom
#: blackboard://content-resource/<file_id>/ URLs.
DOCUMENT_URL_REGEX = re.compile(r"onedrive:\/\/content-resource\/(?P<file_id>.+)")


class OneDriveClient:
    def __init__(
        self, http_service, oauth2_token_service, client_id, client_secret, redirect_uri
    ):

        self._http_service = http_service
        self._oauth2_token_service = oauth2_token_service

        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def get_token(self, code):
        print("GET TOKEN")
        print(
            {
                "client_id": self._client_id,
                "redirect_uri": self._redirect_uri,
                "client_secret": self._client_secret,
                "code": code,
                "grant_type": "authorization_code",
            }
        )
        response = self._http_service.post(
            "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            data={
                "client_id": self._client_id,
                "redirect_uri": self._redirect_uri,
                "client_secret": self._client_secret,
                "code": code,
                "grant_type": "authorization_code",
            },
            schema=OAuthTokenResponseSchema,
        )

        # Save the access token to the DB.
        self._oauth2_token_service.save(
            "graph.microsoft.com",
            response.validated_data["access_token"],
            response.validated_data.get("refresh_token"),
            response.validated_data.get("expires_in"),
        )

    def download_url(self, document_url):
        print(document_url)
        file_id = DOCUMENT_URL_REGEX.search(document_url)["file_id"]

        response = self._http_service.get(
            f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content",
            oauth=True,
        )


def factory(_context, request):
    settings = request.registry.settings

    return OneDriveClient(
        http_service=request.find_service(name="http"),
        oauth2_token_service=request.find_service(name="oauth2_token"),
        client_id=settings["onedrive_client_id"],
        client_secret=settings["onedrive_secret"],
        redirect_uri=request.route_url("onedrive.oauth.callback"),
    )
