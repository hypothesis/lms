from typing import Optional

from lms.models._hashed_id import hashed_id
from lms.models.grouping import Grouping
from lms.services.course import CourseService
from lms.models.grouping import CanvasGroup, CanvasSection, Grouping, GroupingMembership
from lms.models._hashed_id import hashed_id
from lms.models import User, ApplicationInstance

from typing import List, Optional
from lms.models import CanvasGroup, CanvasSection, Grouping, GroupingMembership
from typing import List, Optional, Union

from lms.models import (
    ApplicationInstance,
    CanvasGroup,
    CanvasSection,
    Grouping,
    GroupingMembership,
    User,
)
from sqlalchemy.orm import aliased
from lms.models._hashed_id import hashed_id
from lms.models.grouping import CanvasGroup, CanvasSection, Grouping, GroupingMembership
from lms.services import CourseService


class GroupingService:
    def __init__(self, db, application_instance_service):
        self._db = db
        self._application_instance = application_instance_service.get_current()

    @staticmethod
    def generate_authority_provided_id(
        tool_consumer_instance_guid,
        lms_id,
        parent: Optional[Grouping],
        type_: Grouping.Type,
    ):
        if type_ == Grouping.Type.CANVAS_SECTION:
            return hashed_id(tool_consumer_instance_guid, parent.lms_id, lms_id)
        if type_ == Grouping.Type.COURSE:
            return CourseService.generate_authority_provided_id(
                tool_consumer_instance_guid, lms_id
            )

        return hashed_id(
            tool_consumer_instance_guid,
            parent.lms_id if parent else None,
            type_,
            lms_id,
        )

    def upsert_with_parent(  # pylint: disable=too-many-arguments
        self,
        tool_consumer_instance_guid,
        lms_id,
        lms_name,
        parent: Optional[Grouping],
        type_: Grouping.Type,
        extra=None,
    ):
        """
        Upsert a Grouping generating the authority_provided_id based on its parent.

        :param tool_consumer_instance_guid: Tool consumer GUID
        :param lms_id: ID of this grouping on the LMS
        :param lms_name: Name of the grouping on the LMS
        :param parent: Parent of grouping
        :param type_: Type of the grouping
        :param extra: Any extra information to store linked to this grouping
        """
        return self._upsert(
            Grouping(
                application_instance=self._application_instance,
                authority_provided_id=self.generate_authority_provided_id(
                    tool_consumer_instance_guid, lms_id, parent, type_
                ),
                lms_id=lms_id,
                lms_name=lms_name,
                parent_id=parent.id if parent else None,
                extra=extra,
                type=type_,
            )
        )

    def _upsert(self, grouping):
        db_grouping = (
            self._db.query(Grouping)
            .filter_by(
                application_instance=grouping.application_instance,
                authority_provided_id=grouping.authority_provided_id,
            )
            .one_or_none()
        )
        if not db_grouping:
            self._db.add(grouping)
        else:
            # Update any fields that might have changed
            db_grouping.lms_name = grouping.lms_name
            db_grouping.extra = grouping.extra

        return db_grouping or grouping

    def upsert_with_parent(  # pylint: disable=too-many-arguments
        self,
        tool_consumer_instance_guid,
        lms_id,
        lms_name,
        parent: Grouping,
        type_: Grouping.Type,
        extra=None,
    ):
        """
        Upsert a Grouping generating the authority_provided_id based on its parent.

        :param tool_consumer_instance_guid: Tool consumer GUID
        :param context_id: Course id the group is a part of
        :param group_id: Canvas group id
        :param group_name: The name of the group
        :param group_set_id: Id of the canvas group set this group belongs to
        """
        return self.upsert(
            CanvasGroup(
                application_instance=self._application_instance,
                authority_provided_id=self.generate_authority_provided_id(
                    tool_consumer_instance_guid, lms_id, parent, type_
                ),
                lms_id=lms_id,
                lms_name=lms_name,
                parent_id=parent.id,
                extra=extra,
            )
        )

    def upsert_grouping_memberships(self, user: User, groups: List[Grouping]):
        for group in groups:
            if membership := (
                self._db.query(GroupingMembership)
                .filter_by(grouping_id=group.id, user_id=user.id)
                .one_or_none()
            ):
                continue

            group.memberships.append(GroupingMembership(grouping=group, user=user))

    def get_groupings_for_user(
        self,
        application_instance: ApplicationInstance,
        user_id: str,
        parent_lms_id: Optional[str] = None,
        type_: Optional[Grouping.Type] = None,
        group_set_id: Union[str, int] = None,
    ):
        query = (
            self._db.query(Grouping)
            .join(GroupingMembership)
            .join(User)
            .filter(
                User.user_id == user_id,
                Grouping.application_instance == application_instance,
            )
        )
        if parent_lms_id:
            parent_grouping = aliased(Grouping)
            query = query.join(parent_grouping, Grouping.parent).filter(
                parent_grouping.lms_id == parent_lms_id
            )

        if type_:
            query = query.filter(Grouping.type == type_)

        if group_set_id:
            query = query.filter(
                Grouping.extra["group_set_id"].astext == str(group_set_id)
            )

        return query.all()


def factory(_context, request):
    return GroupingService(
        request.db,
        request.find_service(name="application_instance"),
    )
