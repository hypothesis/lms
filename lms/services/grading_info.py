from marshmallow import fields

from lms.models import GradingInfo
from lms.validation import PyramidRequestSchema, ValidationError

__all__ = ["GradingInfoService"]


class GradingInfoService:
    """Methods for interacting with GradingInfo records."""

    class _ParamsSchema(PyramidRequestSchema):
        """Schema for the relevant parameters from the request."""

        location = "form"
        lis_result_sourcedid = fields.Str(required=True)
        lis_outcome_service_url = fields.Str(required=True)
        context_id = fields.Str(required=True)
        resource_link_id = fields.Str(required=True)
        tool_consumer_info_product_family_code = fields.Str(load_default="")

    def __init__(self, _context, request):
        self._db = request.db
        self._authority = request.registry.settings["h_authority"]

    def get_by_assignment(self, application_instance, context_id, resource_link_id):
        """
        Return all GradingInfo's for a given assignment.

        The returned list will contain one GradingInfo for each student who has
        launched this assignment (and had GradingInfo data persisted for them).

        :param application_instance: the assignment's application_instance
            (identifies a deployment of our app in an LMS)
        :param context_id: the assignment's context_id
            (identifies the course within the LMS)
        :param resource_link_id: the assignment's resource_link_id
            (identifies the assignment within the LMS course)
        """
        return self._db.query(GradingInfo).filter_by(
            application_instance=application_instance,
            context_id=context_id,
            resource_link_id=resource_link_id,
        )

    def upsert_from_request(self, request):
        """
        Update or create a record based on the LTI params found in the request.

        This function will do nothing if the correct parameters cannot be
        found in the request.

        :arg request: A pyramid request
        """
        try:
            parsed_params = self._ParamsSchema(request).parse()
        except ValidationError:
            # We're missing something we need in the request.
            # This can happen if the user is not a student, or if the needed
            # LIS data is not present on the request.
            return

        application_instance = request.find_service(
            name="application_instance"
        ).get_current()

        grading_info = self._find_or_create(
            application_instance=application_instance,
            user_id=request.lti_user.user_id,
            context_id=parsed_params["context_id"],
            resource_link_id=parsed_params["resource_link_id"],
        )
        grading_info.h_username = request.lti_user.h_user.username
        grading_info.h_display_name = request.lti_user.h_user.display_name

        grading_info.update_from_dict(parsed_params)

    def _find_or_create(self, **query):
        result = self._db.query(GradingInfo).filter_by(**query).one_or_none()

        if result is None:
            result = GradingInfo(**query)
            self._db.add(result)

        return result
