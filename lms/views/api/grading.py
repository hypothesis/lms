import datetime
import logging
import re

from pyramid.view import view_config, view_defaults

from lms.error_code import ErrorCode
from lms.events import LTIEvent
from lms.security import Permissions
from lms.services import LTIGradingService
from lms.services.exceptions import ExternalRequestError, SerializableError
from lms.validation import (
    APIReadResultSchema,
    APIRecordResultSchema,
    APIRecordSpeedgraderSchema,
)
from lms.views.helpers import log_retries_callback

LOG = logging.getLogger(__name__)


@view_defaults(request_method="POST", renderer="json", permission=Permissions.API)
class GradingViews:
    """Views for proxy APIs interacting with LTI grading APIs."""

    def __init__(self, request) -> None:
        self.request = request
        self.parsed_params = self.request.parsed_params
        self.lti_grading_service: LTIGradingService = self.request.find_service(
            LTIGradingService
        )

    @view_config(
        route_name="lti_api.result.record",
        schema=APIRecordResultSchema,
        permission=Permissions.GRADE_ASSIGNMENT,
    )
    def record_result(self):
        """Proxy result (grade/score) to LTI Result API."""

        # Fix any float point arithmetic issues
        score = round(self.parsed_params["score"], 4)

        self.lti_grading_service.record_result(
            self.parsed_params["lis_result_sourcedid"],
            score,
            comment=self.parsed_params.get("comment"),
        )
        self.request.registry.notify(
            LTIEvent.from_request(
                request=self.request,
                type_=LTIEvent.Type.GRADE,
                data={
                    "student_user_id": self.parsed_params["student_user_id"],
                    "score": score,
                },
            )
        )

        return {}

    @view_config(
        route_name="lti_api.result.read",
        request_method="GET",
        schema=APIReadResultSchema,
        permission=Permissions.GRADE_ASSIGNMENT,
    )
    def read_result(self):
        """Proxy request for current result (grade/score) to LTI Result API."""

        result = self.lti_grading_service.read_result(
            self.parsed_params["lis_result_sourcedid"]
        )

        return {"currentScore": result.score, "comment": result.comment}

    @view_config(
        route_name="lti_api.submissions.record", schema=APIRecordSpeedgraderSchema
    )
    def record_canvas_speedgrader_submission(self):
        """
        Record info to allow later grading of an assignment via Canvas Speedgrader.

        When a learner launches an assignment the LMS provides metadata that can
        be later used to submit a score to the LMS using LTI APIs.

        In Canvas, extensions to that API allow a custom LTI launch URL to be
        submitted for use by the SpeedGrader [1].

        This view only supports SpeedGrader-based grading in Canvas by
        submitting an LTI Launch URL to Canvas.

        This work _could_ be done by the backend during an LTI launch, but as it
        involves potentially slow requests to the external LMS, it is triggered
        asynchronously by the frontend while the assignment is loading.

        [1] https://canvas.instructure.com/doc/api/file.assignment_tools.html
        """

        # Send the SpeedGrader LTI launch URL to the Canvas instance, if we haven't
        # already created a submission OR if the existing submission has not been
        # graded (Canvas's result-reading API doesn't allow us to distinguish
        # absence of a submission from an ungraded submission. Non-Canvas LMSes in
        # theory require a grade).

        lis_result_sourcedid = self.parsed_params["lis_result_sourcedid"]
        try:
            # If we already have a score, then we've already recorded this info
            if self.lti_grading_service.read_result(lis_result_sourcedid).score:
                LOG.debug(
                    "Grade already present, not recording submission. User ID: %s",
                    self.request.user.id,
                )
                return None

            self.lti_grading_service.record_result(
                lis_result_sourcedid, pre_record_hook=CanvasPreRecordHook(self.request)
            )

        except ExternalRequestError as err:
            if err.is_timeout:
                # We'll inform the frontend that this is a retryable error for timeouts.
                err.retryable = True
                raise

            if (
                err.status_code == 422
                # This is LTI1.3 only. In LTI1.1 canvas behaves differently and allows this type of submissions.
                and "maximum number of allowed attempts has been reached"
                in err.response.text
            ):
                raise SerializableError(
                    error_code=ErrorCode.CANVAS_SUBMISSION_MAX_ATTEMPTS
                ) from err

            # This is Canvas only, we do the error handling here instead of the view to avoid
            # conflicting different, more general use cases.
            # This is what we get with the Course Participation end date has passed.
            if re.search(
                # LTI1.1 and LTI 1.3 strings respectively.
                # The LTI1.3 can happen in both reading and record operations.
                r"Course not available for student|This course has concluded",
                getattr(getattr(err, "response", None), "text", ""),
            ):
                raise SerializableError(
                    error_code=ErrorCode.CANVAS_SUBMISSION_COURSE_NOT_AVAILABLE
                ) from err

            raise err  # noqa: TRY201

        self.request.registry.notify(
            LTIEvent.from_request(request=self.request, type_=LTIEvent.Type.SUBMISSION)
        )
        self.request.add_finished_callback(log_retries_callback)
        return {}


class CanvasPreRecordHook:
    # For details of Canvas extensions to the standard LTI request see:
    # https://erau.instructure.com/doc/api/file.assignment_tools.html

    # We use a set date in the past when no other date is available to avoid creating new submissions.
    DEFAULT_SUBMISSION_DATE = datetime.datetime(2001, 1, 1, tzinfo=datetime.UTC)

    def __init__(self, request):
        self.request = request

    def __call__(self, score=None, request_body=None) -> dict:  # noqa: ARG002
        speedgrader_url = self.get_speedgrader_launch_url()

        #  A `datetime.datetime` that indicates when the submission was
        # created. This is only used in Canvas and is displayed in the
        # SpeedGrader as the submission date. If the submission date matches
        # an existing submission then the existing submission is updated
        # rather than creating a new submission.
        submitted_at = (
            self.request.parsed_params.get("submitted_at")
            or self.DEFAULT_SUBMISSION_DATE
        )

        if "resultRecord" in request_body:
            return self._rewrite_v11(request_body, speedgrader_url, submitted_at)

        return self._rewrite_v13(request_body, speedgrader_url, submitted_at)

    def get_speedgrader_launch_url(self):
        parsed_params = self.request.parsed_params
        params = {
            "focused_user": parsed_params["h_username"],
            "learner_canvas_user_id": parsed_params["learner_canvas_user_id"],
            "group_set": parsed_params.get("group_set"),
            "resource_link_id": parsed_params.get("resource_link_id"),
        }

        params["url"] = parsed_params["document_url"]
        # **WARNING**
        #
        # Canvas has a bug with handling of percent-encoded characters in the
        # the SpeedGrader launch URL. Code that responds to the launch will
        # need to handle this for fields that may contain such chars (eg.
        # the "url" field).
        #
        # See https://github.com/instructure/canvas-lms/issues/1486

        return self.request.route_url("lti_launches", _query=params)

    @staticmethod
    def _rewrite_v11(request_body, speedgrader_url, submitted_at):
        request_body["resultRecord"].setdefault("result", {})["resultData"] = {
            "ltiLaunchUrl": speedgrader_url
        }
        request_body["submissionDetails"] = {"submittedAt": submitted_at}

        return request_body

    @staticmethod
    def _rewrite_v13(request_body, speedgrader_url, submitted_at):
        request_body["https://canvas.instructure.com/lti/submission"] = {
            "submission_type": "basic_lti_launch",
            "submission_data": speedgrader_url,
            "submitted_at": submitted_at.isoformat(),
        }

        return request_body
