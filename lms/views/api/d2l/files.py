"""Proxy API views for files-related D2L API endpoints."""
import re

from pyramid.view import view_config, view_defaults

from lms.product.d2l import D2L
from lms.security import Permissions
from lms.views import helpers
from lms.services import D2LAPIClient

#: A regex for parsing just the file_id part out of one of our custom
#: d2l://content-resource/<file_id>/ URLs.
DOCUMENT_URL_REGEX = re.compile(r"d2l:\/\/content-resource\/(?P<file_path>.*)")


@view_defaults(permission=Permissions.API, renderer="json")
class D2LFilesAPIViews:
    def __init__(self, request):
        self.request = request
        self.d2l_api_client = request.find_service(D2LAPIClient)

    @view_config(request_method="GET", route_name="d2l_api.courses.files.list")
    def list_files(self):
        """Return the list of files in the given course or folder."""

        course_id = self.request.matchdict["course_id"]
        folder_id = self.request.matchdict.get("folder_id")

        results = self.d2l_api_client.course_table_of_contents(course_id).json()

        response_results = []
        for module in results["Modules"]:
            # Does the FE support returning the whole folder structure in one go?
            response_results.append(
                {
                    "display_name": module["Title"],
                    "updated_at": module["LastModifiedDate"],
                    "type": "Folder",
                    "id": module["ModuleId"],
                    "parent_id": None,
                }
            )

            for topic in module["Topics"]:
                if topic["TypeIdentifier"] != "File":
                    continue
                response_results.append(
                    {
                        "display_name": topic["Title"],
                        "updated_at": topic["LastModifiedDate"],
                        "type": "File",
                        # If want the complete folder structure we'd need itkj
                        # we need to take it from here
                        # we also need to remove /content/enforced/6782-DTC101/
                        "id": f"d2l://content-resource/{topic['Url']}",
                        "parent_id": module["ModuleId"],
                    }
                )

        return response_results

    @view_config(request_method="GET", route_name="d2l_api.files.via_url")
    def via_url(self):
        """Return the Via URL for annotating the given D2L file."""

        course_id = self.request.matchdict["course_id"]
        document_url = self.request.params["document_url"]
        print(document_url)
        file_path = DOCUMENT_URL_REGEX.search(document_url)["file_path"]

        file_path = file_path.replace("/content/enforced/6782-DTC101/", "")

        public_url = self.d2l_api_client.public_url(course_id, file_path)

        via_url = helpers.via_url(self.request, public_url, content_type="pdf")

        #
        # NO via pdf gets downloaded
        # return {"via_url": public_url}
        return {"via_url": via_url}


"""
/d2l/api/le/(version)/(orgUnitId)/content/toc

https://docs.valence.desire2learn.com/res/course.html#get--d2l-api-lp-(version)-(orgUnitId)-managefiles-filekjhttps://docs.valence.desire2learn.com/res/content.html#get--d2l-api-le-(version)-(orgUnitId)-content-toc
"""
