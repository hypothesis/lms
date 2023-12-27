from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services import JSTORService


@view_defaults(renderer="json", permission=Permissions.API)
class JSTORAPIViews:
    def __init__(self, request) -> None:
        self.request = request
        self.jstor_service: JSTORService = request.find_service(iface=JSTORService)

    @view_config(route_name="jstor_api.articles.metadata")
    def article_metadata(self):
        return self.jstor_service.get_article_metadata(
            article_id=self.request.matchdict["article_id"]
        )

    @view_config(route_name="jstor_api.articles.thumbnail")
    def article_thumbnail(self):
        # The image is wrapped in an object to make API responses more uniform
        # for consumers.
        return {
            "image": self.jstor_service.thumbnail(
                article_id=self.request.matchdict["article_id"]
            )
        }
