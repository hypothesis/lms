from functools import lru_cache
from typing import Literal, Mapping, NotRequired, Type, TypedDict
from urllib.parse import urlencode, urljoin, urlparse, urlunparse

import requests
from marshmallow import EXCLUDE, Schema, fields, post_load
from pyramid.httpexceptions import HTTPBadRequest

from lms.js_config_types import APICallInfo
from lms.models.oauth2_token import Service
from lms.models.user import User
from lms.services.aes import AESService
from lms.services.exceptions import (
    ExternalRequestError,
    OAuth2TokenError,
    SerializableError,
)
from lms.services.oauth_http import OAuthHTTPService
from lms.services.oauth_http import factory as oauth_http_factory
from lms.validation._base import RequestsResponseSchema


class PaginationSchema(Schema):
    """
    Schema for `meta` field in paginated Canvas Studio responses.

    See `PaginationMeta` on https://tw.instructuremedia.com/api/public/docs/.
    """

    class Meta:
        unknown = EXCLUDE

    current_page = fields.Integer()
    """1-based page number."""

    last_page = fields.Integer()
    """1-based number of last page."""


MAX_PAGE_SIZE = 50
"""Maximum value for `per_page` argument to paginated API calls."""


class CanvasStudioCollectionsSchema(RequestsResponseSchema):
    """Schema for Canvas Studio /collections responses."""

    class CollectionSchema(Schema):
        class Meta:
            unknown = EXCLUDE

        id = fields.Integer(required=True)
        name = fields.Str(required=True, allow_none=True)
        type = fields.Str(required=True)
        created_at = fields.Str(required=False)

    collections = fields.List(fields.Nested(CollectionSchema), required=True)
    meta = fields.Nested(PaginationSchema, required=True)


class CanvasStudioCollectionMediaSchema(RequestsResponseSchema):
    """Schema for Canvas Studio /collections/{id}/media responses."""

    class MediaSchema(Schema):
        class Meta:
            unknown = EXCLUDE

        id = fields.Integer(required=True)
        title = fields.Str(required=True)
        created_at = fields.Str(required=False)
        duration = fields.Float(required=False)
        thumbnail_url = fields.Str(required=False)

    media = fields.List(fields.Nested(MediaSchema), required=True)
    meta = fields.Nested(PaginationSchema, required=True)


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


class File(TypedDict):
    """Represents a file or folder in an LMS's file storage."""

    type: Literal["File", "Folder"]
    mime_type: NotRequired[Literal["text/html", "application/pdf", "video"]]

    id: str
    display_name: str

    duration: NotRequired[float]
    """Duration of media in seconds."""

    updated_at: str
    thumbnail_url: NotRequired[str]

    contents: NotRequired[APICallInfo]
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

    page_size: int
    """Number of items to fetch per page."""

    def __init__(self, request, application_instance, page_size=MAX_PAGE_SIZE):
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
        self._application_instance = application_instance
        self.page_size = page_size

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
            prevent_concurrent_refreshes=True,
        )

    def refresh_admin_access_token(self):
        """Refresh the existing admin access token for Canvas Studio API calls."""

        try:
            self._admin_oauth_http.refresh_access_token(
                self._token_url(),
                self.redirect_uri(),
                auth=(self._client_id, self._client_secret),
                prevent_concurrent_refreshes=True,
            )
        except ExternalRequestError as refresh_err:
            raise SerializableError(
                error_code="canvas_studio_admin_token_refresh_failed",
                message="Canvas Studio admin token refresh failed.",
            ) from refresh_err

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

        collections = self._paginated_api_request(
            "v1/collections", CanvasStudioCollectionsSchema, field="collections"
        )
        user_collection = None

        files: list[File] = []
        for collection in collections:
            if collection["type"] == "user":
                user_collection = collection
                continue

            collection_id = collection["id"]
            files.append(
                {
                    "type": "Folder",
                    "display_name": collection["name"] or f"Collection {collection_id}",
                    "updated_at": collection["created_at"],
                    "id": str(collection_id),
                    "contents": {
                        "path": self._request.route_url(
                            "canvas_studio_api.collections.media.list",
                            collection_id=collection["id"],
                        )
                    },
                }
            )

        # Sort folders by name, then list files after.
        files.sort(key=lambda f: f["display_name"])

        if user_collection:
            files += self.list_collection(str(user_collection["id"]))

        return files

    def list_collection(self, collection_id: str) -> list[File]:
        """List the videos in a collection."""

        media = self._paginated_api_request(
            f"v1/collections/{collection_id}/media",
            CanvasStudioCollectionMediaSchema,
            field="media",
        )

        files: list[File] = []
        for item in media:
            media_id = item["id"]
            files.append(
                {
                    "type": "File",
                    "mime_type": "video",
                    "id": f"canvas-studio://media/{media_id}",
                    "display_name": item["title"],
                    "duration": item.get("duration", None),
                    "updated_at": item["created_at"],
                    # nb. There is a known issue with thumbnails for audio files
                    # where the API returns a thumbnail URL, which redirects to
                    # a `default_thumbnail` image when requested, but that URL
                    # fails to load with a 403.
                    #
                    # We handle this on the frontend by rendering fallback
                    # content if the thumbnail fails to load for any reason.
                    "thumbnail_url": item.get("thumbnail_url", None),
                }
            )

        files.sort(key=lambda f: f["display_name"])

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

    def get_video_download_url(self, media_id: str) -> str | None:
        """
        Return temporary download URL for a video.

        This may return `None` if the video is not available for download.
        This can happen for videos imported into Canvas Studio from YouTube
        or Vimeo.

        Security: This method does not check whether the current user should
        have access to this video. See `_admin_api_request`.
        """

        try:
            download_rsp = self._bare_api_request(
                f"v1/media/{media_id}/download", as_admin=True, allow_redirects=False
            )
        except ExternalRequestError as err:
            # Canvas Studio returns 422 if the video is not available for download.
            if err.status_code == 422:
                return None
            raise

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

        Security: This method does not check whether the current user should
        have access to this video. See `_admin_api_request`.
        """

        captions = self._api_request(
            f"v1/media/{media_id}/caption_files",
            CanvasStudioCaptionFilesSchema,
            as_admin=True,
        )

        for caption in captions:
            if caption["status"] == "published":
                url = urljoin(self._canvas_studio_site(), caption["url"])
                return url

        return None

    def _api_request(
        self,
        path: str,
        schema_cls: Type[RequestsResponseSchema],
        as_admin=False,
    ) -> dict:
        """
        Make a request to the Canvas Studio API and parse the JSON response.

        :param path: Request path, relative to the API root
        :param schema_cls: Schema to parse the JSON response
        :param as_admin: Make the request using the admin account instead of the current user.
        """
        response = self._bare_api_request(path, as_admin=as_admin)
        return schema_cls(response).parse()

    def _paginated_api_request(
        self,
        path: str,
        schema_cls: Type[RequestsResponseSchema],
        field: str,
        as_admin=False,
    ) -> list:
        """
        Fetch a paginated collection via the Canvas Studio API.

        :param path: Request path, relative to the API root
        :param schema_cls: Schema to parse the JSON response
        :param field: Response field containing items from each page
        :param as_admin: Make the request using the admin account instead of the current user.
        """
        max_pages = 100
        next_page = 1
        last_page = None
        collated = []

        while last_page is None or next_page <= last_page:
            params = {"page": next_page, "per_page": self.page_size}
            response = self._bare_api_request(path, as_admin=as_admin, params=params)
            parsed = schema_cls(response).parse()
            collated += parsed[field]
            last_page = min(parsed["meta"]["last_page"], max_pages)
            next_page += 1

        return collated

    def _admin_api_request(self, path: str, allow_redirects=True) -> requests.Response:
        """
        Make a request to the Canvas Studio API using the admin user identity.

        This method should not be used if the current user _is_ the admin user.
        In that case we want to follow the normal steps for making a request
        using the current identity, and the corresponding error handling.

        Security: Since this method makes requests as an admin user it does not
        take account of whether the current user _should_ have access to a
        particular video. Be sure to only make requests for videos where this
        has been established some other way (eg. by its association with the
        assignment being launched).
        """

        url = self._api_url(path)
        try:
            return self._admin_oauth_http.get(url, allow_redirects=allow_redirects)
        except ExternalRequestError as err:
            refreshable = getattr(err.response, "status_code", None) == 401
            if not refreshable:
                # Ordinarily if the access token is missing or expired, we'll
                # return an error and the frontend will prompt to
                # re-authenticate. That won't help for admin-authenticated
                # requests.
                if isinstance(err, OAuth2TokenError):
                    raise HTTPBadRequest(
                        "The Canvas Studio admin needs to authenticate the Hypothesis integration"
                    ) from err
                raise

            raise OAuth2TokenError(
                refreshable=True,
                refresh_route="canvas_studio_api.oauth.refresh_admin",
                refresh_service=Service.CANVAS_STUDIO,
            ) from err

    def _bare_api_request(
        self,
        path: str,
        as_admin=False,
        allow_redirects=True,
        params: Mapping[str, str | int] | None = None,
    ) -> requests.Response:
        """
        Make a request to the Canvas Studio API and return the response.

        :param as_admin: Make the request using the admin account instead of the current user.
        """
        url = self._api_url(path, params)

        if as_admin and not self.is_admin():
            return self._admin_api_request(path, allow_redirects=allow_redirects)

        try:
            return self._oauth_http_service.get(url, allow_redirects=allow_redirects)
        except ExternalRequestError as err:
            refreshable = getattr(err.response, "status_code", None) == 401
            if not refreshable:
                raise

            raise OAuth2TokenError(
                refreshable=True,
                refresh_route="canvas_studio_api.oauth.refresh",
                refresh_service=Service.CANVAS_STUDIO,
            ) from err

    def _api_url(self, path: str, params: Mapping[str, str | int] | None = None) -> str:
        """
        Return the URL of a Canvas Studio API endpoint.

        See https://tw.instructuremedia.com/api/public/docs/ for available
        endpoints.

        :param path: Path of endpoint relative to the API root
        :param params: Query parameters
        """

        site = self._canvas_studio_site()
        url = f"{site}/api/public/{path}"
        if params:
            url = url + "?" + urlencode(params)
        return url

    def _admin_email(self) -> str:
        """Return the email address of the configured Canvas Studio admin."""
        admin_email = self._application_instance.settings.get(
            "canvas_studio", "admin_email"
        )
        if not admin_email:
            raise HTTPBadRequest(
                "Admin account is not configured for Canvas Studio integration"
            )
        return admin_email

    def is_admin(self) -> bool:
        """Return true if the current LTI user is the configure Canvas Studio admin."""
        return self._request.lti_user.email == self._admin_email()

    @property
    @lru_cache
    def _admin_oauth_http(self) -> OAuthHTTPService:
        """
        Return an OAuthHTTPService that makes calls using the admin user account.

        Admin accounts have the ability to download all videos and transcripts
        in a Canvas Studio instance, whereas videos can ordinarily only be
        downloaded by the owner. Therefore when launching Canvas Studio
        assignments, we use this account instead of the current user's account
        to authenticate the API requests for downloading videos and transcripts.
        """

        # The caller should check for this condition before calling this method
        # and use the standard `self._oauth_http_service` property instead.
        assert not self.is_admin()

        admin_email = self._admin_email()
        admin_user = (
            self._request.db.query(User)
            .filter_by(
                email=admin_email, application_instance=self._application_instance
            )
            .one_or_none()
        )
        if not admin_user:
            raise HTTPBadRequest(
                "The Canvas Studio admin needs to authenticate the Hypothesis integration"
            )
        admin_lti_user = admin_user.user_id

        return oauth_http_factory(
            {}, self._request, service=Service.CANVAS_STUDIO, user_id=admin_lti_user
        )

    def _canvas_studio_site(self) -> str:
        return f"https://{self._domain}"


def factory(_context, request):
    return CanvasStudioService(request, request.lti_user.application_instance)
