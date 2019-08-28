import datetime
from datetime import timezone

from pyramid.view import view_config

from lms.validation import APIRecordSubmissionSchema
from lms.services.lti_outcomes import LTIOutcomesRequestParams


@view_config(
    request_method="POST",
    route_name="lti_api.submissions.record",
    renderer="json",
    schema=APIRecordSubmissionSchema,
)
def record_submission(request):
    """
    Record info to facilitate later grading of an assignment.

    When a learner launches an assignment the LMS provides metadata that can
    be later used to submit a score to the LMS using LTI Outcome Management
    APIs. In Canvas, extensions to that API allow a custom LTI launch URL to be
    submitted for use by the SpeedGrader [1].

    Currently this view only supports SpeedGrader-based grading in Canvas by
    submitting an LTI Launch URL to Canvas. In future it will need to persist the
    metadata to facilitate grading in other LMSes via a different UI.

    This work _could_ be done by the backend during an LTI launch, but as it
    involves potentially slow requests to the external LMS, it is triggered
    asynchronously by the frontend while the assignment is loading.

    [1] https://canvas.instructure.com/doc/api/file.assignment_tools.html
    """

    lti_user = request.lti_user
    parsed_params = request.parsed_params

    shared_secret = request.find_service(name="ai_getter").shared_secret(
        lti_user.oauth_consumer_key
    )
    outcome_request_params = LTIOutcomesRequestParams(
        consumer_key=lti_user.oauth_consumer_key,
        shared_secret=shared_secret,
        lis_outcome_service_url=parsed_params["lis_outcome_service_url"],
        lis_result_sourcedid=parsed_params["lis_result_sourcedid"],
    )

    lti_outcomes_client = request.find_service(name="lti_outcomes_client")

    # Send the SpeedGrader LTI launch URL to the Canvas instance, if we haven't
    # already created a submission OR if the existing submission has not been
    # graded (Canvas's result-reading API doesn't allow us to distinguish
    # absence of a submission from an ungraded submission. Non-Canvas LMSes in
    # theory require a grade).
    current_score = lti_outcomes_client.read_result(outcome_request_params)
    if current_score is None:
        # **WARNING**
        #
        # Canvas has a bug with handling of percent-encoded characters in the
        # the SpeedGrader launch URL. Code that responds to the launch will
        # need to handle this for fields that may contain such chars (eg.
        # the "url" field).
        #
        # See https://github.com/instructure/canvas-lms/issues/1486
        speedgrader_launch_params = {"focused_user": parsed_params["h_username"]}
        if parsed_params.get("document_url"):
            speedgrader_launch_params["url"] = parsed_params.get("document_url")
        elif parsed_params.get("canvas_file_id"):
            speedgrader_launch_params["canvas_file"] = "true"
            speedgrader_launch_params["file_id"] = parsed_params["canvas_file_id"]

        speedgrader_launch_url = request.route_url(
            "lti_launches", _query=speedgrader_launch_params
        )

        lti_outcomes_client.record_result(
            outcome_request_params,
            lti_launch_url=speedgrader_launch_url,
            submitted_at=datetime.datetime(2001, 1, 1, tzinfo=timezone.utc),
        )

    return {}


@view_config(
    request_method="POST",
    route_name="lti_api.submissions.submit_grade",
    renderer="json",
)
def submit_grade(request):
    lti_user = request.lti_user

    shared_secret = request.find_service(name="ai_getter").shared_secret(
        lti_user.oauth_consumer_key
    )

    outcome_request_params = LTIOutcomesRequestParams(
        consumer_key=lti_user.oauth_consumer_key,
        shared_secret=shared_secret,
        lis_outcome_service_url=request.json["lis_outcome_service_url"],
        lis_result_sourcedid=request.json["lis_result_sourcedid"],
    )

    request.find_service(name="lti_outcomes_client").record_result(
        outcome_request_params, score=request.json["score"]
    )

    return {}
