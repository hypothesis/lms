from typing import Iterable

from lms.models.lti_params import CLAIM_PREFIX, LTIParamPlugin


class CanvasLTIParamPlugin(LTIParamPlugin):
    # Add all the basic params in addition to some of our own
    v13_parameter_map: Iterable = list(LTIParamPlugin.v13_parameter_map) + [
        (
            "custom_canvas_course_id",
            [f"{CLAIM_PREFIX}/custom", "canvas_course_id"],
        ),
        (
            "custom_canvas_api_domain",
            [f"{CLAIM_PREFIX}/custom", "canvas_api_domain"],
        ),
        (
            "custom_canvas_user_id",
            [f"{CLAIM_PREFIX}/custom", "canvas_user_id"],
        ),
    ]

    @classmethod
    def modify_params(cls, lti_params, request):
        # In LTI1.3 some custom canvas parameters are sent as integers
        # and as a string in LTI1.1.
        for canvas_param_name in ["custom_canvas_course_id", "custom_canvas_user_id"]:
            canvas_param_value = lti_params.get(canvas_param_name)
            if isinstance(canvas_param_value, int):
                lti_params[canvas_param_name] = str(canvas_param_value)

        # Canvas SpeedGrader launches LTI apps with the wrong resource_link_id,
        # see:
        #
        # * https://github.com/instructure/canvas-lms/issues/1952
        # * https://github.com/hypothesis/lms/issues/3228
        #
        # We add the correct resource_link_id as a query param on the launch
        # URL that we submit to Canvas and use that instead of the incorrect
        # resource_link_id that Canvas puts in the request's body.
        is_speedgrader = request.params.get("learner_canvas_user_id")

        if is_speedgrader and (
            resource_link_id := request.params.get("resource_link_id")
        ):
            lti_params["resource_link_id"] = resource_link_id

        return lti_params
