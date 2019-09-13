from lms.models import LISResultSourcedId

__all__ = ["LISResultSourcedIdService"]


class LISResultSourcedIdService:
    """Methods for interacting with LISResultSourcedId records."""

    def __init__(self, _context, request):
        self._db = request.db

    def upsert(self, lis_info, h_user, lti_user):
        """
        Update an existing record or create a new one if none exists.

        :arg lis_info: LIS-specific attrs
        :type lis_info: :class:`lms.values.LISResultSourcedId`
        :arg h_user: The h user this record is associated with
        :type h_user: :class:`lms.values.HUser`
        :arg lti_user: The LTI-provided user that this record is associated with
        :type lti_user: :class:`lms.values.LTIUser`
        :return: The new or updated record
        :rtype: :class:`~lms.models.LISResultSourcedId`
        """
        lis_result_sourcedid = (
            self._db.query(LISResultSourcedId)
            .filter_by(
                oauth_consumer_key=lti_user.oauth_consumer_key,
                user_id=lti_user.user_id,
                context_id=lis_info.context_id,
                resource_link_id=lis_info.resource_link_id,
            )
            .one_or_none()
        )

        if lis_result_sourcedid is None:
            lis_result_sourcedid = LISResultSourcedId(
                oauth_consumer_key=lti_user.oauth_consumer_key,
                user_id=lti_user.user_id,
                context_id=lis_info.context_id,
                resource_link_id=lis_info.resource_link_id,
            )
            self._db.add(lis_result_sourcedid)

        lis_result_sourcedid.lis_result_sourcedid = lis_info.lis_result_sourcedid
        lis_result_sourcedid.lis_outcome_service_url = lis_info.lis_outcome_service_url

        lis_result_sourcedid.h_username = h_user.username
        lis_result_sourcedid.h_display_name = h_user.display_name

        lis_result_sourcedid.tool_consumer_info_product_family_code = (
            lis_info.tool_consumer_info_product_family_code
        )

        return lis_result_sourcedid
