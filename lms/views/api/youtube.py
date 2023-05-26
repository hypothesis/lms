from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services import YoutubeService


@view_defaults(renderer="json", permission=Permissions.API)
class YouTubeAPIViews:
    def __init__(self, request):
        self.request = request
        self.youtube_service: YoutubeService = request.find_service(iface=YoutubeService)

    @view_config(route_name="youtube_api.videos")
    def video_info(self):
        # The image is wrapped in an object to make API responses more uniform
        # for consumers.
        return {
            "image": "https://i.ytimg.com/vi/EU6TDnV5osM/mqdefault.jpg",
            "title": "Hypothesis and Atlassian New Partnership Announced at the Team23 Conference",
            "channel": "Hypothesis",
            "duration": "PT2M20S"  # ISO duration
        }
