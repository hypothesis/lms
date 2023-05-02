class YoutubeService:
    """An interface for dealing with Youtube API."""

    def __init__(self, enabled: bool):
        """
        Initialise the Youtube service.

        :param enabled: Whether Youtube is enabled on this instance
        """
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        """Get whether this instance is configured for Youtube."""

        return self._enabled


def factory(_context, request):
    ai_settings = (
        request.find_service(name="application_instance").get_current().settings
    )
    return YoutubeService(enabled=ai_settings.get("youtube", "enabled"))
