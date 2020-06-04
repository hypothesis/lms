import requests
from pyramid.view import view_config, view_defaults


@view_defaults(permission="vitalsource_api", renderer="json")
class VitalSourceAPIViews:
    def __init__(self, request):
        self.request = request
        self._api_key = request.registry.settings["vitalsource_api_key"]

        if not self._api_key:
            raise Exception("VitalSource API key is not set")

    @view_config(request_method="GET", route_name="vitalsource_api.books.list")
    def list_books(self):
        """
        List the books available to the current user.
        """
        # data = self._call_vitalsource_api("products")
        # items = data["items"]

        # FIXME - Fetch just the one book from the VS catalog that is set up
        # for Hypothesis. A configuration issue on their end is causing "products"
        # to return other books as well.
        data = self._call_vitalsource_api("products/HYPOTHESIS-TESTING")
        items = [data]

        items.sort(key=lambda item: item["title"].lower())

        # The "products" API can return individual books which have a VBID
        # and collections (called "packages") which do not. Ignore packages
        # for now.
        items = [item for item in items if item["vbid"]]

        def _format_item(item):
            return {
                "id": item["vbid"],
                "title": item["title"],
                "cover_image": item["resource_links"].get("cover_image"),
            }

        return [_format_item(item) for item in items]

    @view_config(request_method="GET", route_name="vitalsource_api.books.toc")
    def book_toc(self):
        """
        Get the chapters for the current book.
        """
        book_id = self.request.matchdict["book_id"]
        data = self._call_vitalsource_api(f"products/{book_id}/toc")

        def _format_item(item):
            return {
                "title": item["title"],
                "cfi": item.get("cfi"),
                "page": item.get("page"),
            }

        return [_format_item(item) for item in data["table_of_contents"]]

    def _call_vitalsource_api(self, path, params={}):
        response = requests.get(
            f"https://api.vitalsource.com/v4/{path}",
            headers={
                "Accept": "application/json",
                "X-VitalSource-API-Key": self._api_key,
            },
            params=params,
        )

        # TODO - Translate into standard API error.
        response.raise_for_status()

        # TODO - Validate response structure against expected schema.
        return response.json()
