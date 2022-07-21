from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services import JSTORService


@view_defaults(renderer="json", permission=Permissions.API)
class JSTORAPIViews:
    def __init__(self, request):
        self.request = request
        self.jstor_service: JSTORService = request.find_service(iface=JSTORService)

    @view_config(route_name="jstor_api.articles.metadata")
    def article_metadata(self):
        article_id = self.request.matchdict["article_id"]
        article_info = self.jstor_service.metadata(article_id)
        content_status = article_info["content_status"]

        return {
            "title": article_info["title"],
            "content_status": content_status.name.lower(),
        }

    @view_config(route_name="jstor_api.articles.thumbnail")
    def article_thumbnail(self):
        article_id = self.request.matchdict["article_id"]
        data_uri = self.jstor_service.thumbnail(article_id)

        # The image is wrapped in an object to make API responses more uniform
        # for consumers.
        return {"image": data_uri}
