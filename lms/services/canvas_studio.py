from typing import Literal, Optional, TypedDict
from urllib.parse import urlencode, urlunparse

from marshmallow import EXCLUDE, Schema, fields, post_load

from lms.models.oauth2_token import Service
from lms.services.aes import AESService
from lms.services.oauth_http import factory as oauth_http_factory
from lms.validation._base import RequestsResponseSchema


class CanvasStudioCollectionsSchema(RequestsResponseSchema):
    """Schema for Canvas Studio /collections responses."""

    class CollectionSchema(Schema):
        class Meta:
            unknown = EXCLUDE

        id = fields.Integer(required=True)
        name = fields.Str(required=True)
        type = fields.Str(required=True)
        created_at = fields.Str(required=False)

    collections = fields.List(fields.Nested(CollectionSchema), required=True)

    @post_load
    def post_load(self, data, **_kwargs):
        return data["collections"]


class CanvasStudioCollectionMediaSchema(RequestsResponseSchema):
    """Schema for Canvas Studio /collections/{id}/media responses."""

    class MediaSchema(Schema):
        class Meta:
            unknown = EXCLUDE

        id = fields.Integer(required=True)
        title = fields.Str(required=True)
        created_at = fields.Str(required=False)

    media = fields.List(fields.Nested(MediaSchema), required=True)

    @post_load
    def post_load(self, data, **_kwargs):
        return data["media"]


class APICallInfo(TypedDict):
    path: str
    authUrl: str | None


class File(TypedDict):
    """Represents a file or folder in an LMS's file storage."""

    type: Literal["File", "Folder"]

    id: str
    display_name: str
    updated_at: str

    contents: Optional[APICallInfo]
    """API call to use to fetch contents of a folder."""


class CanvasStudioService:
    """
    Service for authenticating with and making calls to the Canvas Studio API.

    Useful links:

        Authorization guide: https://community.canvaslms.com/t5/Canvas-Studio-Blog/Connecting-Studio-OAuth-via-Postman/ba-p/259739
        API reference: https://tw.instructuremedia.com/api/public/docs/
    """

    def __init__(self, request, application_instance):
        self._domain = application_instance.settings.get("canvas_studio", "domain")
        self._client_id = application_instance.settings.get(
            "canvas_studio", "client_id"
        )
        self._client_secret = application_instance.settings.get_secret(
            request.find_service(AESService), "canvas_studio", "client_secret"
        )
        self._oauth_http_service = oauth_http_factory(
            {}, request, service=Service.CANVAS_STUDIO
        )
        self._request = request

    def get_access_token(self, code: str) -> None:
        """
        Fetch and persist an access token for Canvas Studio API calls.

        :param code: Authorization code received from OAuth callback
        """
        token_url = self._api_url("oauth/token")
        self._oauth_http_service.get_access_token(
            token_url,
            self.redirect_uri(),
            auth=(self._client_id, self._client_secret),
            authorization_code=code,
        )

    def authorization_url(self, state: str) -> str:
        """
        Construct the authorization endpoint URL for Canvas Studio.

        This constructs the authorization URL for the Canvas Studio instance
        associated with the current application instance.

        :param state: `state` query param for the authorization request
        """
        auth_url = urlunparse(
            (
                "https",
                self._domain,
                "api/public/oauth/authorize",
                "",
                urlencode(
                    {
                        "client_id": self._client_id,
                        "response_type": "code",
                        "redirect_uri": self.redirect_uri(),
                        "state": state,
                    }
                ),
                "",
            )
        )

        return auth_url

    def redirect_uri(self) -> str:
        """Return OAuth redirect URI for Canvas Studio."""
        return self._request.route_url("canvas_studio_api.oauth.callback")

    def list_media_library(self) -> list[File]:
        """
        List the videos and collections for the current user.

        The result of this call corresponds to what the user sees if they
        visit Canvas Studio from within their LMS, or use the Canvas Studio
        picker when creating a Page.
        """

        collections = self._api_request("v1/collections", CanvasStudioCollectionsSchema)
        user_collection = None

        files = []
        for collection in collections:
            if collection["type"] == "user":
                user_collection = collection
                continue

            files.append(
                {
                    "type": "Folder",
                    "display_name": collection["name"],
                    "updated_at": collection["created_at"],
                    "id": str(collection["id"]),
                    "contents": {
                        "path": self._request.route_url(
                            "canvas_studio_api.collections.media.list",
                            collection_id=collection["id"],
                        )
                    },
                }
            )

        if user_collection:
            files += self.list_collection(str(user_collection["id"]))

        return files

    def list_collection(self, collection_id: str) -> list[File]:
        """List the videos in a collection."""

        media = self._api_request(
            f"v1/collections/{collection_id}/media", CanvasStudioCollectionMediaSchema
        )

        files = []
        for item in media:
            media_id = item["id"]
            files.append(
                {
                    "type": "File",
                    "id": f"canvas-studio://media/{media_id}",
                    "display_name": item["title"],
                    "updated_at": item["created_at"],
                }
            )

        return files

    def _api_request(self, path: str, schema_cls: RequestsResponseSchema) -> dict:
        """Make a request to the Canvas Studio API and parse the JSON response."""
        response = self._oauth_http_service.get(self._api_url(path))
        return schema_cls(response).parse()

    def _api_url(self, path: str) -> str:
        """
        Return the URL of a Canvas Studio API endpoint.

        See https://tw.instructuremedia.com/api/public/docs/ for available
        endpoints.

        :param path: Path of endpoint relative to the API root
        """

        site = self._canvas_studio_site()
        return f"{site}/api/public/{path}"

    def _canvas_studio_site(self) -> str:
        return f"https://{self._domain}"


def factory(_context, request):
    return CanvasStudioService(request, request.lti_user.application_instance)
