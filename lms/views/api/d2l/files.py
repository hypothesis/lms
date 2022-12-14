from pyramid.view import view_config

from lms.security import Permissions
from lms.services.d2l_api import D2LAPIClient


def _find_files(modules):
    """Recursively find files in modules."""
    for module in modules:
        for topic in module.get("topics", []):
            if topic.get("type") == "File":
                yield topic

        # Find submodules
        yield from _find_files(module.get("modules", []))


@view_config(
    request_method="GET",
    route_name="d2l_api.courses.files.list",
    renderer="json",
    permission=Permissions.API,
)
def list_files(_context, request):
    """Return the list of files in the given course."""
    modules = request.find_service(D2LAPIClient).course_table_of_contents(
        org_unit=request.matchdict["course_id"]
    )
    return [
        {
            "id": f"d2l://content-resource/{file['id']}/",
            "display_name": file["name"],
            "updated_at": file["updated_at"],
            "type": "File",
        }
        for file in _find_files(modules)
    ]
