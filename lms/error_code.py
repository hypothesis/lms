"""
Error codes are useful in different parts of the application.

We have them in their own module to avoid any circular dependency problems.
"""

from enum import StrEnum


class ErrorCode(StrEnum):
    BLACKBOARD_MISSING_INTEGRATION = "blackboard_missing_integration"
    CANVAS_INVALID_SCOPE = "canvas_invalid_scope"
    VITALSOURCE_STUDENT_PAY_NO_LICENSE = "vitalsource_student_pay_no_license"
    VITALSOURCE_STUDENT_PAY_LICENSE_LAUNCH = "vitalsource_student_pay_license_launch"
    VITALSOURCE_STUDENT_PAY_LICENSE_LAUNCH_INSTRUCTOR = (
        "vitalsource_student_pay_license_launch_instructor"
    )
    REUSED_CONSUMER_KEY = "reused_consumer_key"
    CANVAS_SUBMISSION_COURSE_NOT_AVAILABLE = "canvas_submission_course_not_available"
    CANVAS_SUBMISSION_MAX_ATTEMPTS = "canvas_submission_max_attempts"

    OAUTH2_AUTHORIZATION_ERROR = "oauth2_authorization_error"
    """Show the authorization dialog on the front end."""
