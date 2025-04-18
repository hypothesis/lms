import sys

from factory.alchemy import SQLAlchemyModelFactory

from tests.factories import requests_ as requests
from tests.factories.application_instance import ApplicationInstance
from tests.factories.assignment import Assignment, AutoGradingConfig
from tests.factories.assignment_grouping import AssignmentGrouping
from tests.factories.assignment_membership import (
    AssignmentMembership,
    LMSUserAssignmentMembership,
)
from tests.factories.attributes import (
    ACCESS_TOKEN,
    H_DISPLAY_NAME,
    H_USERNAME,
    OAUTH_CONSUMER_KEY,
    REFRESH_TOKEN,
    RESOURCE_LINK_ID,
    SHARED_SECRET,
    TOOL_CONSUMER_INSTANCE_GUID,
    USER_ID,
)
from tests.factories.dashboard_admin import DashboardAdmin
from tests.factories.event import Event, EventData
from tests.factories.file import File
from tests.factories.grading_info import GradingInfo
from tests.factories.grading_sync import GradingSync, GradingSyncGrade
from tests.factories.group_info import GroupInfo
from tests.factories.grouping import BlackboardGroup, CanvasGroup, CanvasSection, Course
from tests.factories.grouping_membership import GroupingMembership
from tests.factories.h_user import HUser
from tests.factories.hubspot_company import HubSpotCompany
from tests.factories.jwt_oauth2_token import JWTOAuth2Token
from tests.factories.lms_course import (
    LMSCourse,
    LMSCourseApplicationInstance,
    LMSCourseMembership,
)
from tests.factories.lms_group_set import LMSGroupSet
from tests.factories.lms_segment import LMSSegment, LMSSegmentMembership
from tests.factories.lms_user import LMSUser, LMSUserApplicationInstance
from tests.factories.lti_registration import LTIRegistration
from tests.factories.lti_role import LTIRole, LTIRoleOverride
from tests.factories.lti_user import LTIUser
from tests.factories.notification import Notification
from tests.factories.oauth2_token import OAuth2Token
from tests.factories.organization import Organization
from tests.factories.organization_usage import OrganizationUsageReport
from tests.factories.roster import AssignmentRoster, CourseRoster, LMSSegmentRoster
from tests.factories.rsa_key import RSAKey
from tests.factories.task_done import TaskDone
from tests.factories.user import User
from tests.factories.user_preferences import UserPreferences
