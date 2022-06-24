import pytest

from lms.models import LTIParams
from lms.product.canvas._plugin.lti_params import CanvasLTIParamPlugin


class TestCanvasLTIParamPlugin:
    @pytest.mark.parametrize(
        "field_name", ("custom_canvas_course_id", "custom_canvas_user_id")
    )
    @pytest.mark.parametrize("value", [123, "123"])
    def test_modify_params_stringifies_int_params(
        self, pyramid_request, field_name, value
    ):
        lti_params = LTIParams({field_name: value})

        lti_params = CanvasLTIParamPlugin.modify_params(lti_params, pyramid_request)

        assert lti_params[field_name] == str(value)

    @pytest.mark.parametrize(
        "speedgrader,expected",
        (("any_value", "canvas_value"), (None, "standard_value")),
    )
    def test_modify_params_reads_resource_link_id_in_speedgrader(
        self, pyramid_request, speedgrader, expected
    ):
        lti_params = LTIParams({"resource_link_id": "standard_value"})
        pyramid_request.params["resource_link_id"] = "canvas_value"
        pyramid_request.params["learner_canvas_user_id"] = speedgrader

        lti_params = CanvasLTIParamPlugin.modify_params(lti_params, pyramid_request)

        assert lti_params["resource_link_id"] == expected
