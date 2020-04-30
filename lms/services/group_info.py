"""A service that upserts :class:`lms.models.GroupInfoService` records."""

from lms.models import GroupInfo

__all__ = ["GroupInfoService"]


class GroupInfoService:  # pylint:disable=too-few-public-methods
    """
    A service that upserts :class:`~lms.models.GroupInfo` records.

    Usage::

        group_info = request.find_service(name="group_info")
        group_info.upsert(authority_provided_id, consumer_key, request.params)
    """

    def __init__(self, _context, request):
        self._db = request.db
        self._lti_user = request.lti_user

    def upsert(self, authority_provided_id, consumer_key, params):
        """
        Upsert a row into the ``group_info`` DB table.

        Find the :class:`~lms.models.GroupInfo` with the given
        ``authority_provided_id``, or create it if none exists.  Then update
        the ``GroupInfo``'s ``consumer_key`` to the given ``consumer_key``, and
        update its other columns from the items in ``params``.

        ``params["id"]`` and ``params["authority_provided_id"]`` will be
        ignored if present--these columns can't be updated.

        Any keys in ``params`` that don't correspond to a ``GroupInfo`` column
        name will be ignored.

        :param authority_provided_id: the ``authority_provided_id`` of the
            ``GroupInfo`` to create or update
        :param consumer_key: the ``GroupInfo.consumer_key`` value to set
        :param params: the other ``GroupInfo`` columns to set
        :type params: dict
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
        group_info.update_from_dict(
            params, skip_keys={"authority_provided_id", "id", "info"}
        )

        if self._lti_user.is_instructor:
            group_info.upsert_instructor(self._lti_user.h_user._asdict())
