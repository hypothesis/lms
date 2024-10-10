from lms.services.exceptions import SerializableError
from lms.services.http import HTTPService

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"
"""YouTube's API base URL"""


class VideoNotFound(SerializableError):  # noqa: N818
    def __init__(self, video_id):
        super().__init__(
            error_code="youtube_video_not_found", details={"video_id": video_id}
        )


class YouTubeService:
    """An interface for dealing with YouTube API."""

    def __init__(self, enabled: bool, api_key: str, http: HTTPService):
        """
        Initialise the YouTube service.

        :param enabled: Whether YouTube is enabled on this instance
        :param api_key: YouTube API key
        """
        self._enabled = enabled
        self._api_key = api_key
        self._http = http

    @property
    def enabled(self) -> bool:
        """Get whether this instance is configured for YouTube."""

        return bool(self._enabled and self._api_key)

    def video_info(self, video_id: str) -> dict:
        """
        Fetch YouTube video information.

        :param video_id: A YouTube video ID
        :raise VideoNotFound: If the video cannot be found
        """

        # Endpoint docs: https://developers.google.com/youtube/v3/docs/videos/list
        json_resp: dict = self._http.get(
            url=f"{YOUTUBE_API_URL}/videos",
            params={
                "id": video_id,
                "key": self._api_key,
                "part": "contentDetails,snippet,status",
                "maxResults": "1",
            },
        ).json()

        try:
            item = json_resp["items"][0]
        except IndexError as err:
            raise VideoNotFound(video_id) from err

        snippet = item["snippet"]
        content_details = item.get("contentDetails", {})
        restrictions = self._resolve_video_restrictions(item)

        return {
            "image": snippet["thumbnails"]["medium"]["url"],
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "duration": content_details["duration"],  # ISO duration
            "restrictions": restrictions,
        }

    def _resolve_video_restrictions(self, item: dict) -> list[str]:
        restrictions: list[str] = []

        # Check if the video is age restricted
        if (
            item.get("contentDetails", {}).get("contentRating", {}).get("ytRating", "")
            == "ytAgeRestricted"
        ):
            restrictions.append("age")

        # Check if the video does not allow embedding
        if not item.get("status", {}).get("embeddable", True):
            restrictions.append("no_embed")

        return restrictions


def factory(_context, request) -> YouTubeService:
    ai_settings = request.lti_user.application_instance.settings
    app_settings = request.registry.settings

    return YouTubeService(
        enabled=ai_settings.get("youtube", "enabled", True),
        api_key=app_settings.get("youtube_api_key"),
        http=request.find_service(name="http"),
    )
