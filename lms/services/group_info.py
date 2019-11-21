"""A service that upserts :class:`lms.models.GroupInfoService` records."""

from lms.models import GroupInfo

__all__ = ["GroupInfoService"]


class GroupInfoService:
    """
    A service that upserts :class:`lms.models.GroupInfoService` records.

    Usage:

        group_info = request.find_service(name="group_info")
        group_info.upsert(authority_provided_id, consumer_key, request.params)
    """

    # GroupInfo columns that upsert() *doesn't* update, even if they're in the given params.
    SKIP_COLUMNS = {"authority_provided_id", "id"}

    def __init__(self, _context, request):
        self._db = request.db

    def upsert(self, authority_provided_id, consumer_key, params):
        """
        Upsert a row into the group_info DB table.

        Finds a ``GroupInfoService`` row if available, and creates it if not, setting
        the ``consumer_key`` and relevant values from ``params``.

        :param authority_provided_id: The value to find the group by
        :param consumer_key: The consumer key to update
        :param params: A dict of values to pick relevant items from
        """
        group_info = (
            self._db.query(GroupInfo)
            .filter_by(authority_provided_id=authority_provided_id)
            .one_or_none()
        )

        if not group_info:
            group_info = GroupInfo(
                authority_provided_id=authority_provided_id, consumer_key=consumer_key
            )
            self._db.add(group_info)

        group_info.consumer_key = consumer_key
        group_info.update_from_dict(params, skip_keys=self.SKIP_COLUMNS)
