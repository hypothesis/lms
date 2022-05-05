from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services import LTIGradingService
from lms.validation import (
    APIReadResultSchema,
    APIRecordResultSchema,
    APIRecordSpeedgraderSchema,
)


@view_defaults(request_method="POST", renderer="json", permission=Permissions.API)
class LTIOutcomesViews:
    """Views for proxy APIs interacting with LTI Outcome Management APIs."""

    def __init__(self, request):
        self.request = request
        self.parsed_params = self.request.parsed_params
        self.lti_grading_service: LTIGradingService = self.request.find_service(
            LTIGradingService
        )

    @view_config(route_name="lti_api.result.record", schema=APIRecordResultSchema)
    def record_result(self):
        """Proxy result (grade/score) to LTI Outcomes Result API."""

        self.lti_grading_service.record_result(
            self.parsed_params["lis_result_sourcedid"],
            score=self.parsed_params["score"],
        )

        return {}

    @view_config(
        route_name="lti_api.result.read",
        request_method="GET",
        schema=APIReadResultSchema,
    )
    def read_result(self):
        """Proxy request for current result (grade/score) to LTI Outcomes Result API."""

        current_score = self.lti_grading_service.read_result(
            self.parsed_params["lis_result_sourcedid"]
        )

        return {"currentScore": current_score}

    @view_config(
        route_name="lti_api.submissions.record", schema=APIRecordSpeedgraderSchema
    )
    def record_canvas_speedgrader_submission(self):
        """
        Record info to allow later grading of an assignment via Canvas Speedgrader.

        When a learner launches an assignment the LMS provides metadata that can
        be later used to submit a score to the LMS using LTI Outcome Management
        APIs. In Canvas, extensions to that API allow a custom LTI launch URL to be
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

        # If we already have a score, then we've already recorded this info
        if self.lti_grading_service.read_result(lis_result_sourcedid):
            return None

        self.lti_grading_service.record_result(
            lis_result_sourcedid,
            canvas_extensions=LTIGradingService.CanvasExtensions(
                lti_launch_url=get_speedgrader_launch_url(self.request),
                submitted_at=self.request.parsed_params.get("submitted_at"),
            ),
        )

        return {}


def get_speedgrader_launch_url(request):
    parsed_params = request.parsed_params
    params = {
        "focused_user": parsed_params["h_username"],
        "learner_canvas_user_id": parsed_params["learner_canvas_user_id"],
        "group_set": parsed_params.get("group_set"),
        "ext_lti_assignment_id": parsed_params.get("ext_lti_assignment_id"),
        "resource_link_id": parsed_params.get("resource_link_id"),
    }

    if parsed_params.get("document_url"):
        params["url"] = parsed_params.get("document_url")
    elif book_id := parsed_params.get("vitalsource_book_id"):
        params["vitalsource_book"] = "true"
        params["book_id"] = book_id
        params["cfi"] = parsed_params["vitalsource_cfi"]
    else:
        assert parsed_params.get("canvas_file_id"), (
            "All Canvas launches should have either a 'document_url' a 'vitalsource_book_id' or "
            "a 'canvas_file_id' parameter."
        )
        params["canvas_file"] = "true"
        params["file_id"] = parsed_params["canvas_file_id"]

    # **WARNING**
    #
    # Canvas has a bug with handling of percent-encoded characters in the
    # the SpeedGrader launch URL. Code that responds to the launch will
    # need to handle this for fields that may contain such chars (eg.
    # the "url" field).
    #
    # See https://github.com/instructure/canvas-lms/issues/1486

    return request.route_url("lti_launches", _query=params)
