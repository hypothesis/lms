from lms.models._mixins import CreatedUpdatedMixin
from lms.models.application_instance import ApplicationInstance, ApplicationSettings
from lms.models.assignment import (
    Assignment,
    AutoGradingCalculation,
    AutoGradingConfig,
    AutoGradingType,
)
from lms.models.assignment_grouping import AssignmentGrouping
from lms.models.assignment_membership import (
    AssignmentMembership,
    LMSUserAssignmentMembership,
)
from lms.models.course_groups_exported_from_h import CourseGroupsExportedFromH
from lms.models.dashboard_admin import DashboardAdmin
from lms.models.event import Event, EventData, EventType, EventUser
from lms.models.exceptions import ReusedConsumerKey
from lms.models.family import Family
from lms.models.file import File
from lms.models.grading_info import GradingInfo
from lms.models.grading_sync import GradingSync, GradingSyncGrade
from lms.models.group_info import GroupInfo
from lms.models.group_set import LMSGroupSet
from lms.models.grouping import (
    BlackboardGroup,
    CanvasGroup,
    CanvasSection,
    Course,
    Grouping,
    GroupingMembership,
)
from lms.models.h_user import HUser
from lms.models.hubspot import HubSpotCompany
from lms.models.json_settings import JSONSettings
from lms.models.jwt_oauth2_token import JWTOAuth2Token
from lms.models.legacy_course import LegacyCourse
from lms.models.lms_course import (
    LMSCourse,
    LMSCourseApplicationInstance,
    LMSCourseMembership,
)
from lms.models.lms_segment import LMSSegment, LMSSegmentMembership
from lms.models.lms_term import LMSTerm
from lms.models.lms_user import LMSUser, LMSUserApplicationInstance
from lms.models.lti_params import CLAIM_PREFIX, LTIParams
from lms.models.lti_registration import LTIRegistration
from lms.models.lti_role import LTIRole, LTIRoleOverride, RoleScope, RoleType
from lms.models.lti_user import LTIUser, display_name
from lms.models.notification import Notification
from lms.models.oauth2_token import OAuth2Token
from lms.models.organization import Organization
from lms.models.organization_usage import OrganizationUsageReport
from lms.models.roster import AssignmentRoster, CourseRoster, LMSSegmentRoster
from lms.models.rsa_key import RSAKey
from lms.models.task_done import TaskDone
from lms.models.user import User
from lms.models.user_preferences import UserPreferences


def includeme(_config):
    pass
