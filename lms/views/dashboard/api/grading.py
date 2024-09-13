import logging

from marshmallow import Schema, fields
from pyramid.view import view_config
from sqlalchemy import select

from lms.models import GradingSync, GradingSyncGrade, LMSUser
from lms.security import Permissions
from lms.services.dashboard import DashboardService
from lms.validation._base import JSONPyramidRequestSchema
from lms.tasks.grading import sync_grades

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
    def create_auto_grading_sync(self):
        assignment = self.dashboard_service.get_request_assignment(self.request)

        if self.db.scalar(
            select(GradingSync).where(
                GradingSync.assignment_id == assignment.id,
                GradingSync.status.in_(["scheduled", "in_progress"]),
            )
        ):
            return 409

        grading_sync = GradingSync(assignment_id=assignment.id, status="scheduled")
        self.db.add(grading_sync)
        self.db.flush()
        sync_h_user_ids = [g["h_userid"] for g in self.request.parsed_params["grades"]]
        sync_lms_users = self.request.db.execute(
            select(LMSUser.h_userid, LMSUser.id).where(
                LMSUser.h_userid.in_(sync_h_user_ids)
            )
        ).all()
        # Organize the data in a dict h_userid -> lti_user_id for easier access
        sync_lms_users_by_h_userid = {r[0]: r[1] for r in sync_lms_users}
        for grade in self.request.parsed_params["grades"]:
            self.db.add(
                GradingSyncGrade(
                    grading_sync_id=grading_sync.id,
                    lms_user_id=sync_lms_users_by_h_userid[grade["h_userid"]],
                    grade=grade["grade"],
                )
            )
        self.request.db.flush()
        self.request.add_finished_callback(lambda _: sync_grades.apply_async(()))
        return {}

    @view_config(
        route_name="api.dashboard.assignments.grading.sync",
        request_method="GET",
        renderer="json",
        permission=Permissions.GRADE_ASSIGNMENT,
    )
    def get_auto_grading_sync(self):
        assignment = self.dashboard_service.get_request_assignment(self.request)

        if grading_sync := self.db.scalar(
            select(GradingSync).where(
                GradingSync.assignment_id == assignment.id,
                GradingSync.status.in_("scheduled", "in_progress"),
            )
        ):
            return grading_sync

        return {}
