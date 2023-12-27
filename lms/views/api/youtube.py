from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services import YouTubeService


@view_defaults(renderer="json", permission=Permissions.API)
class YouTubeAPIViews:
    def __init__(self, request) -> None:
        self.request = request
        self.youtube_service: YouTubeService = request.find_service(
            iface=YouTubeService
        )

    @view_config(route_name="youtube_api.videos")
    def video_info(self) -> dict:
        video_id = self.request.matchdict["video_id"]
        return self.youtube_service.video_info(video_id)
