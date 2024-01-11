from lms.models._mixins import CreatedUpdatedMixin
from lms.models.application_instance import ApplicationInstance, ApplicationSettings
from lms.models.assignment import Assignment
from lms.models.assignment_grouping import AssignmentGrouping
from lms.models.assignment_membership import AssignmentMembership
from lms.models.course import LegacyCourse
from lms.models.course_groups_exported_from_h import CourseGroupsExportedFromH
from lms.models.event import Event, EventData, EventType, EventUser
from lms.models.exceptions import ReusedConsumerKey
from lms.models.file import File
from lms.models.grading_info import GradingInfo
from lms.models.group_info import GroupInfo
from lms.models.grouping import (
    BlackboardGroup,
    CanvasGroup,
    CanvasSection,
    Course,
    Grouping,
    GroupingMembership,
)
from lms.models.h_user import HUser
from lms.models.json_settings import JSONSettings
from lms.models.jwt_oauth2_token import JWTOAuth2Token
from lms.models.lti_params import CLAIM_PREFIX, LTIParams
from lms.models.lti_registration import LTIRegistration
from lms.models.lti_role import LTIRole, LTIRoleOverride
from lms.models.lti_user import LTIUser, display_name
from lms.models.oauth2_token import OAuth2Token
from lms.models.organization import Organization
from lms.models.region import Region
from lms.models.rsa_key import RSAKey
from lms.models.task_done import TaskDone
from lms.models.user import User
from lms.models.user_preferences import UserPreferences


def includeme(_config):
    pass
