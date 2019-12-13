import os
from logging import getLogger
from urllib.parse import urlparse

from lms.logic.grading import grading_types
from lms.services.tool_consumer.generic_service import ToolConsumerService
from lms.tool_consumer.moodle import MoodleClient
from lms.tool_consumer.moodle.model import GradeType

LOG = getLogger(__name__)


class MoodleInterface(ToolConsumerService):
    product_family_code = "moodle"

    def __init__(self, context, request):
        super().__init__(context, request)

        self.moodle_api = None
        self.moodle_api = self._get_moodle_api(request)

    @classmethod
    def _get_moodle_api(cls, request):
        launch_url = request.params.get("launch_presentation_return_url")
        base_url = urlparse(launch_url)._replace(query=None, path="").geturl()

        return MoodleClient(
            base_url=base_url,
            # TODO: How the hell can we get this?
            ws_token=os.environ["JONS_SPECIAL_DEBUGGING_WS_TOKEN"],
        )

    def grading_type(self, resource_link_id):
        module = self._get_module(resource_link_id)

        grade_type = module.grade_type

        if grade_type == GradeType.SCALE:
            return grading_types.EnumeratedGrading(module.scale.values_as_dict())

        if grade_type == GradeType.POINT:
            return grading_types.FloatGrading(min=0, max=module.max_grade)

        return None

    def requires_grading_ui(self, resource_link_id):
        return self._get_module(resource_link_id).is_gradable

    def _get_module(self, resource_link_id):
        # TODO! - We should cache these calls.
        return self.moodle_api.course.get_course_module_by_instance(
            "lti", resource_link_id
        )
