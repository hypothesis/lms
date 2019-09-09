from lms.models import LISResultSourcedId

__all__ = ["LISResultSourcedIdService"]


class LISResultSourcedIdService:
    """Methods for interacting with LISResultSourcedId records."""

    def __init__(self, _context, request):
        self._db = request.db

    def upsert(self, validated_attrs):
        """
        Update an existing record or create a new one if none exists.

        :arg validated_attrs: Valid attributes for associated
            :class:`lms.models.LISResultSourcedId` record.
        :return: The new or updated record
        :rtype: :class:`~lms.models.LISResultSourcedId`
        """
        lis_result_sourcedid = (
            self._db.query(LISResultSourcedId)
            .filter_by(
                oauth_consumer_key=validated_attrs["oauth_consumer_key"],
                user_id=validated_attrs["user_id"],
                context_id=validated_attrs["context_id"],
                resource_link_id=validated_attrs["resource_link_id"],
            )
            .one_or_none()
        )

        if lis_result_sourcedid is None:
            lis_result_sourcedid = LISResultSourcedId(
                oauth_consumer_key=validated_attrs["oauth_consumer_key"],
                user_id=validated_attrs["user_id"],
                context_id=validated_attrs["context_id"],
                resource_link_id=validated_attrs["resource_link_id"],
            )
            self._db.add(lis_result_sourcedid)

        lis_result_sourcedid.lis_result_sourcedid = validated_attrs[
            "lis_result_sourcedid"
        ]
        lis_result_sourcedid.lis_outcome_service_url = validated_attrs[
            "lis_outcome_service_url"
        ]
        lis_result_sourcedid.h_username = validated_attrs["h_username"]
        lis_result_sourcedid.h_display_name = validated_attrs["h_display_name"]

        if "tool_consumer_info_product_family_code" in validated_attrs:
            lis_result_sourcedid.tool_consumer_info_product_family_code = validated_attrs[
                "tool_consumer_info_product_family_code"
            ]

        return lis_result_sourcedid
