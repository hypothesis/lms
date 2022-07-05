from lms.product.plugin import LTILaunchPlugin
from tests.unit.lms.resources.oauth2_redirect_test import JSConfig


class CanvasLTILaunchPlugin(LTILaunchPlugin):
    supports_grading_bar = False

    def add_to_launch_js_config(self, js_config: JSConfig):
        return
