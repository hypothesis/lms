from typing import Literal, NotRequired, Type, TypedDict
from urllib.parse import urlencode, urljoin, urlparse, urlunparse

from marshmallow import EXCLUDE, Schema, fields, post_load

from lms.models.oauth2_token import Service
from lms.services.aes import AESService
from lms.services.exceptions import ExternalRequestError, OAuth2TokenError
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


class CanvasStudioCaptionFilesSchema(RequestsResponseSchema):
    """Schema for Canvas Studio /media/{id}/caption_files responses."""

    class CaptionFile(Schema):
        class Meta:
            unknown = EXCLUDE

        status = fields.Str(required=True)
        url = fields.Str(required=False)
        """Download URL for the transcript. Not required if `status` is not "published"."""

    caption_files = fields.List(fields.Nested(CaptionFile), required=True)

    @post_load
    def post_load(self, data, **_kwargs):
        return data["caption_files"]


class APICallInfo(TypedDict):
    path: str
    authUrl: str | None


class File(TypedDict):
    """Represents a file or folder in an LMS's file storage."""

    type: Literal["File", "Folder"]
    mime_type: NotRequired[Literal["text/html", "application/pdf", "video"]]

    id: str
    display_name: str
    updated_at: str

    contents: APICallInfo | None
    """API call to use to fetch contents of a folder."""


def replace_localhost_in_url(url: str) -> str:
    """
    Replace references to the standard dev server host with `hypothesis.local`.

    This is a workaround for constraints on redirect URIs in Canvas Studio's
    OAuth implementation. See comments in `lms.views.api.canvas_studio`.
    """
    localhost_prefix = "http://localhost:8001/"
    if not url.startswith(localhost_prefix):
        return url
    return url.replace(localhost_prefix, "https://hypothesis.local:48001/")


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
        self._oauth_http_service.get_access_token(
            self._token_url(),
            self.redirect_uri(),
            auth=(self._client_id, self._client_secret),
            authorization_code=code,
        )

    def refresh_access_token(self):
        """Refresh the existing access token for Canvas Studio API calls."""
        self._oauth_http_service.refresh_access_token(
            self._token_url(),
            self.redirect_uri(),
            auth=(self._client_id, self._client_secret),
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

    def _token_url(self) -> str:
        """Return the URL of the Canvas Studio OAuth token endpoint."""
        return self._api_url("oauth/token")

    def redirect_uri(self) -> str:
        """Return OAuth redirect URI for Canvas Studio."""
        redirect_uri = self._request.route_url("canvas_studio_api.oauth.callback")
        return replace_localhost_in_url(redirect_uri)

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
                    "mime_type": "video",
                    "id": f"canvas-studio://media/{media_id}",
                    "display_name": item["title"],
                    "updated_at": item["created_at"],
                }
            )

        return files

    @classmethod
    def media_id_from_url(cls, url: str) -> str | None:
        """Extract the media ID from a `canvas-studio://media/{media_id}` assignment URL."""
        parsed = urlparse(url)
        if parsed.scheme != "canvas-studio" or parsed.netloc != "media":
            return None
        return parsed.path[1:]

    def get_canonical_video_url(self, media_id: str) -> str:
        """Return the URL to associate with annotations on a Canvas Studio video."""
        # We use the REST resource URL as a stable URL for the video.
        # Example: "https://hypothesis.instructuremedia.com/api/public/v1/media/4"
        return self._api_url(f"v1/media/{media_id}")

    def get_video_download_url(self, media_id: str) -> str:
        """Return temporary download URL for a video."""

        download_url = self._api_url(f"v1/media/{media_id}/download")
        download_rsp = self._oauth_http_service.get(download_url, allow_redirects=False)
        download_redirect = download_rsp.headers.get("Location")

        if download_rsp.status_code != 302 or not download_redirect:
            raise ExternalRequestError(
                message="Media download did not return valid redirect",
                response=download_rsp,
            )

        return download_redirect

    def get_transcript_url(self, media_id: str) -> str | None:
        """
        Return URL of transcript for a video, in SRT (SubRip) format.

        May return `None` if no transcript has been generated for the video.
        """

        captions = self._api_request(
            f"v1/media/{media_id}/caption_files", CanvasStudioCaptionFilesSchema
        )

        for caption in captions:
            if caption["status"] == "published":
                url = urljoin(self._canvas_studio_site(), caption["url"])
                return url

        return None

    def _api_request(self, path: str, schema_cls: Type[RequestsResponseSchema]) -> dict:
        """Make a request to the Canvas Studio API and parse the JSON response."""
        try:
            response = self._oauth_http_service.get(self._api_url(path))
        except ExternalRequestError as err:
            refreshable = getattr(err.response, "status_code", None) == 401
            if refreshable:
                raise OAuth2TokenError(
                    refreshable=True,
                    refresh_route="canvas_studio_api.oauth.refresh",
                    refresh_service=Service.CANVAS_STUDIO,
                ) from err

            raise

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
