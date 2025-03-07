import logging

from marshmallow import Schema, fields, validate
from pyramid.view import view_config
from sqlalchemy import select

from lms.models import GradingSync, LMSUser
from lms.models.grading_sync import AutoGradingSyncStatus
from lms.security import Permissions
from lms.services import AutoGradingService
from lms.services.dashboard import DashboardService  # noqa: TC001
from lms.tasks.grading import sync_grades
from lms.validation._base import JSONPyramidRequestSchema

LOG = logging.getLogger(__name__)


class _GradeSchema(Schema):
    h_userid = fields.Str(required=True)
    grade = fields.Float(required=True)


class AutoGradeSyncSchema(JSONPyramidRequestSchema):
    grades = fields.List(
        fields.Nested(_GradeSchema), required=True, validate=validate.Length(min=1)
    )


class DashboardGradingViews:
    def __init__(self, request) -> None:
        self.request = request
        self.db = request.db
        self.dashboard_service: DashboardService = request.find_service(
            name="dashboard"
        )
        self.auto_grading_service: AutoGradingService = request.find_service(
            AutoGradingService
        )

    @view_config(
        route_name="api.dashboard.assignments.grading.sync",
        request_method="POST",
        renderer="json_iso_utc",
        permission=Permissions.GRADE_ASSIGNMENT,
        schema=AutoGradeSyncSchema,
    )
    def create_grading_sync(self):
        assignment = self.dashboard_service.get_request_assignment(
            self.request, self.request.matchdict["assignment_id"]
        )

        if self.auto_grading_service.get_in_progress_sync(assignment):
            self.request.response.status_int = 400
            return {"message": "There's already an auto-grade sync in progress"}

        sync_h_user_ids = [g["h_userid"] for g in self.request.parsed_params["grades"]]
        sync_lms_users = self.db.scalars(
            select(LMSUser).where(LMSUser.h_userid.in_(sync_h_user_ids))
        ).all()
        if not sync_lms_users:
            self.request.response.status_int = 400
            return {
                "message": "No users for this grade sync. Can't find any of the provided users"
            }

        sync_lms_users_by_h_userid: dict[str, LMSUser] = {
            lms_user.h_userid: lms_user for lms_user in sync_lms_users
        }

        lms_user_grades = {
            sync_lms_users_by_h_userid[g["h_userid"]]: g["grade"]
            for g in self.request.parsed_params["grades"]
            if g["h_userid"] in sync_lms_users_by_h_userid
        }
        grading_sync = self.auto_grading_service.create_grade_sync(
            assignment,
            self.request.user.lms_user,
            lms_user_grades,
        )
        self.request.add_finished_callback(self._start_sync_grades)
        return self._serialize_grading_sync(grading_sync)

    @view_config(
        route_name="api.dashboard.assignments.grading.sync",
        request_method="GET",
        renderer="json_iso_utc",
        permission=Permissions.GRADE_ASSIGNMENT,
    )
    def get_grading_sync(self):
        assignment = self.dashboard_service.get_request_assignment(
            self.request, self.request.matchdict["assignment_id"]
        )
        if grading_sync := self.auto_grading_service.get_last_sync(assignment):
            return self._serialize_grading_sync(grading_sync)

        self.request.response.status_int = 404
        return {"message": f"No existing grading sync for assignment:{assignment.id}"}

    @staticmethod
    def _start_sync_grades(_request) -> None:
        """Start processing a GradeSync after its creation.
        We use this helper method instead of a lambda to make the test asserts easier.
        """  # noqa: D205
        sync_grades.delay()

    @staticmethod
    def _serialize_grading_sync(grading_sync: GradingSync) -> dict:
        return {
            "status": grading_sync.status,
            "finish_date": grading_sync.updated
            if grading_sync.status
            in {AutoGradingSyncStatus.FINISHED, AutoGradingSyncStatus.FAILED}
            else None,
            "grades": [
                {
                    "h_userid": grade.lms_user.h_userid,
                    "grade": grade.grade,
                    "status": grade.status,
                }
                for grade in grading_sync.grades
            ],
        }
