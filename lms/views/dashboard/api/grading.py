import logging
from datetime import datetime

from marshmallow import Schema, fields
from pyramid.view import view_config
from sqlalchemy import select

from lms.models import (
    ApplicationInstance,
    Grouping,
    LMSUser,
    LTIRegistration,
)
from lms.security import Permissions
from lms.services import LTIAHTTPService
from lms.services.dashboard import DashboardService
from lms.services.lti_grading.factory import LTI13GradingService
from lms.validation._base import JSONPyramidRequestSchema

LOG = logging.getLogger(__name__)


class _GradeSchema(Schema):
    h_userid = fields.Str(required=True)
    grade = fields.Float(required=True)


class AutoGradeSyncSchema(JSONPyramidRequestSchema):
    grades = fields.List(fields.Nested(_GradeSchema), required=True)


class DashboardGradingViews:
    def __init__(self, request) -> None:
        self.request = request
        self.db = request.db
        self.dashboard_service: DashboardService = request.find_service(
            name="dashboard"
        )

    @view_config(
        route_name="api.dashboard.assignments.grading.sync",
        request_method="POST",
        renderer="json",
        permission=Permissions.GRADE_ASSIGNMENT,
        schema=AutoGradeSyncSchema,
    )
    def auto_grading_sync(self):
        assignment = self.dashboard_service.get_request_assignment(self.request)
        assert assignment.lis_outcome_service_url, "Assignment without grading URL"
        lti_registration = self.db.scalars(
            select(LTIRegistration)
            .join(ApplicationInstance)
            .join(Grouping)
            .where(Grouping.id == assignment.course_id)
            .order_by(LTIRegistration.updated.desc())
        ).first()
        assert lti_registration, "No LTI registraion for LTI1.3 assignment"

        sync_h_user_ids = [g["h_userid"] for g in self.request.parsed_params["grades"]]

        sync_lms_users = self.db.execute(
            select(LMSUser.h_userid, LMSUser.lti_v13_user_id).where(
                LMSUser.h_userid.in_(sync_h_user_ids)
            )
        ).all()
        # Organize the data in a dict h_userid -> lti_user_id for easier access
        sync_lms_users_by_h_userid = {r[0]: r[1] for r in sync_lms_users}

        grading_service = LTI13GradingService(
            ltia_service=self.request.find_service(LTIAHTTPService),
            line_item_url=None,
            line_item_container_url=None,
            product_family=None,  # type: ignore
            misc_plugin=None,  # type: ignore
            lti_registration=None,  # type: ignore
        )
        # Use the same timestamp for all grades of the same sync
        grade_sync_time_stamp = datetime.now()
        for grade in self.request.parsed_params["grades"]:
            grading_service.sync_grade(
                lti_registration,
                assignment.lis_outcome_service_url,
                grade_sync_time_stamp,
                sync_lms_users_by_h_userid[grade["h_userid"]],
                grade["grade"],
            )
