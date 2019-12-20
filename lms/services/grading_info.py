from marshmallow import fields

from lms.models import GradingInfo
from lms.validation import PyramidRequestSchema, ValidationError

__all__ = ["GradingInfoService"]


class GradingInfoService:
    """Methods for interacting with GradingInfo records."""

    class _ParamsSchema(PyramidRequestSchema):
        """Schema for the relevant parameters from the request."""

        locations = ["form"]
        lis_result_sourcedid = fields.Str(required=True)
        lis_outcome_service_url = fields.Str(required=True)
        context_id = fields.Str(required=True)
        resource_link_id = fields.Str(required=True)
        tool_consumer_info_product_family_code = fields.Str(missing="")

    def __init__(self, _context, request):
        self._db = request.db
        self._authority = request.registry.settings["h_authority"]

    def get_by_assignment(self, oauth_consumer_key, context_id, resource_link_id):
        """
        Get available grading data for students for an assignment.

        Retrieve all :class:`~lms.models.GradingInfo`s that match this
        assignment (each unique combination of (``oauth_consumer_key``,
        ``context_id``, ``resource_link_id``) corresponds to an assignment).
        There should be one record per applicable student who has launched this
        assignment (and had ``GradingInfo`` data persisted for them).

        :arg oauth_consumer_key: Which LMS application install the request
                                 corresponds to.
        :type oauth_consumer_key: str
        :arg context_id: LTI parameter indicating the course
        :type context_id: str
        :arg resource_link_id: LTI parameter (roughly) equating to an assignment
        :type resource_link_id: str
        :rtype: list[:class:`lms.models.GradingInfo`]
        """
        return (
            self._db.query(GradingInfo)
            .filter_by(
                oauth_consumer_key=oauth_consumer_key,
                context_id=context_id,
                resource_link_id=resource_link_id,
            )
            .all()
        )

    def upsert_from_request(self, request, h_user, lti_user):
        """
        Update or create a record based on the LTI params found in the request.

        This function will do nothing if the correct parameters cannot be
        found in the request.

        :arg request: A pyramid request
        :arg h_user: The h user this record is associated with
        :type h_user: :class:`lms.values.HUser`
        :arg lti_user: The LTI-provided user that this record is associated with
        :type lti_user: :class:`lms.values.LTIUser`
        """
        try:
            parsed_params = self._ParamsSchema(request).parse()
        except ValidationError:
            # We're missing something we need in the request.
            # This can happen if the user is not a student, or if the needed
            # LIS data is not present on the request.
            return

        grading_info = self._find_or_create(
            GradingInfo,
            oauth_consumer_key=lti_user.oauth_consumer_key,
            user_id=lti_user.user_id,
            context_id=parsed_params["context_id"],
            resource_link_id=parsed_params["resource_link_id"],
        )

        grading_info.h_username = h_user.username
        grading_info.h_display_name = h_user.display_name

        grading_info.update_from_dict(parsed_params)

    def _find_or_create(self, model_class, **query):
        result = self._db.query(model_class).filter_by(**query).one_or_none()

        if result is None:
            result = model_class(**query)
            self._db.add(result)

        return result
