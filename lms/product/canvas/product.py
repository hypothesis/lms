from dataclasses import dataclass

from lms.product.canvas._plugin.grouping import CanvasGroupingPlugin
from lms.product.product import PluginConfig, Product, Routes


@dataclass
class Canvas(Product):
    """A product for Canvas specific settings and tweaks."""

    family: Product.Family = Product.Family.CANVAS

    route: Routes = Routes(
        oauth2_authorize="canvas_api.oauth.authorize",
        oauth2_refresh="canvas_api.oauth.refresh",
        list_group_sets="canvas_api.courses.group_sets.list",
    )

    plugin_config: PluginConfig = PluginConfig(grouping=CanvasGroupingPlugin)

    settings_key = "canvas"

    @staticmethod
    def productize_lti_params(request, lti_params):
        print("FOR CANVS")
        # Canvas SpeedGrader launches LTI apps with the wrong resource_link_id,
        # see:
        # * https://github.com/instructure/canvas-lms/issues/1952
        # * https://github.com/hypothesis/lms/issues/3228
        #
        # We add the correct resource_link_id as a query param on the launch
        # URL that we submit to Canvas and use that instead of the incorrect
        # resource_link_id that Canvas puts in the request's body.
        is_speedgrader = request.GET.get("learner_canvas_user_id")

        if is_speedgrader and (resource_link_id := request.GET.get("resource_link_id")):
            lti_params["resource_link_id"] = resource_link_id

        for canvas_param_name in ["custom_canvas_course_id", "custom_canvas_user_id"]:
            # In LTI1.3 some custom canvas parameters were sent as integers
            # and as strings in LTI1.1.
            # With this update:
            #   https://community.canvaslms.com/t5/Canvas-Change-Log/Canvas-Platform-Breaking-Changes/ta-p/262015
            # They should also be strings in LTI1.3 but not all
            # canvas instances run the last version so we are keeping this for some time
            canvas_param_value = lti_params.get(canvas_param_name)
            if isinstance(canvas_param_value, int):
                LOG.debug("Canvas: integer value for %s", canvas_param_name)
                lti_params[canvas_param_name] = str(canvas_param_value)

        return lti_params
