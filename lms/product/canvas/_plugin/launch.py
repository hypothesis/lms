from lms.product.plugin.launch import LaunchPlugin


class CanvasLaunchPlugin(LaunchPlugin):
    def course_extra(self, lti_params):
        return {
            "canvas": {
                "custom_canvas_course_id": lti_params.get("custom_canvas_course_id")
            }
        }
