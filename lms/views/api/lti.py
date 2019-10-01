import datetime
from datetime import timezone

from pyramid.view import view_config, view_defaults

from lms.validation import (
    APIRecordSpeedgraderSchema,
    APIReadResultSchema,
    APIRecordResultSchema,
)
from lms.services.lti_outcomes import LTIOutcomesRequestParams


@view_defaults(request_method="POST", renderer="json", permission="lti_outcomes")
class LTIOutcomesViews:
    """Views for proxy APIs interacting with LTI Outcome Management APIs."""

    def __init__(self, request):
        self.request = request
        self.parsed_params = self.request.parsed_params
        self.lti_outcomes_client = self.request.find_service(name="lti_outcomes_client")

        lti_user = self.request.lti_user

        shared_secret = self.request.find_service(name="ai_getter").shared_secret(
            lti_user.oauth_consumer_key
        )
        self.outcome_request_params = LTIOutcomesRequestParams(
            consumer_key=lti_user.oauth_consumer_key,
            shared_secret=shared_secret,
            lis_outcome_service_url=self.parsed_params["lis_outcome_service_url"],
            lis_result_sourcedid=self.parsed_params["lis_result_sourcedid"],
        )

    @view_config(route_name="lti_api.result.record", schema=APIRecordResultSchema)
    def record_result(self):
        """Proxy result (grade/score) to LTI Outcomes Result API."""

        self.request.find_service(name="lti_outcomes_client").record_result(
            self.outcome_request_params, score=self.request.parsed_params["score"]
        )

        return {}

    @view_config(
        route_name="lti_api.result.read",
        request_method="GET",
        schema=APIReadResultSchema,
    )
    def read_result(self):
        """Proxy request for current result (grade/score) to LTI Outcomes Result API."""

        current_score = self.request.find_service(
            name="lti_outcomes_client"
        ).read_result(self.outcome_request_params)

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
        current_score = self.lti_outcomes_client.read_result(
            self.outcome_request_params
        )
        if current_score is None:
            # **WARNING**
            #
            # Canvas has a bug with handling of percent-encoded characters in the
            # the SpeedGrader launch URL. Code that responds to the launch will
            # need to handle this for fields that may contain such chars (eg.
            # the "url" field).
            #
            # See https://github.com/instructure/canvas-lms/issues/1486
            speedgrader_launch_params = {
                "focused_user": self.parsed_params["h_username"]
            }
            if self.parsed_params.get("document_url"):
                speedgrader_launch_params["url"] = self.parsed_params.get(
                    "document_url"
                )
            elif self.parsed_params.get("canvas_file_id"):
                speedgrader_launch_params["canvas_file"] = "true"
                speedgrader_launch_params["file_id"] = self.parsed_params[
                    "canvas_file_id"
                ]

            speedgrader_launch_url = self.request.route_url(
                "lti_launches", _query=speedgrader_launch_params
            )

            self.lti_outcomes_client.record_result(
                self.outcome_request_params,
                lti_launch_url=speedgrader_launch_url,
                submitted_at=datetime.datetime(2001, 1, 1, tzinfo=timezone.utc),
            )

        return {}
