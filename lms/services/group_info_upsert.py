"""A service that upserts :class:`lms.models.GroupInfo` records."""
from lms.models import GroupInfo

__all__ = ["GroupInfoUpsert"]


class GroupInfoUpsert:
    """
    A callable that upserts :class:`lms.models.GroupInfo` records.

    Usage:

        group_info_upsert = request.find_service(name="group_info_upsert")
        group_info_upsert(authority_provided_id, consumer_key, **kwargs)
    """

    def __init__(self, _context, request):
        self._db = request.db

    def __call__(self, authority_provided_id, consumer_key, **kwargs):
        """
        Upsert a row into the group_info DB table.

        Find the existing group_info with the given ``authority_provided_id``
        and update it with the given ``consumer_key`` and ``kwargs``.

        If no group_info with the given ``authority_provided_id`` exists then
        create one.
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

        for name, value in kwargs.items():
            setattr(group_info, name, value)
