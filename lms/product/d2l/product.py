from dataclasses import dataclass

from lms.product.d2l._plugin.grouping import D2LGroupingPlugin
from lms.product.product import PluginConfig, Product, Routes
from lms.services import LTIGradingService


@dataclass
class D2L(Product):
    """A product for D2L specific settings and tweaks."""

    family: Product.Family = Product.Family.D2L

    plugin_config: PluginConfig = PluginConfig(grouping_service=D2LGroupingPlugin)

    route: Routes = Routes(
        oauth2_authorize="d2l_api.oauth.authorize",
        oauth2_refresh="d2l_api.oauth.refresh",
        list_group_sets="d2l_api.courses.group_sets.list",
    )

    settings_key = "desire2learn"

    def is_gradable(self, lti_params):
        if lti_params["lti_version"] != "1.3.0":
            # D2L doesn't automatically create a line item for assignments by default like it does for 1.1.
            # If we are creating them automatically in our end all of them will be gradable.
            return True

        return super().is_gradable(lti_params)

    def configure_assignment(self, request):
        lti_params = request.lti_params
        resource_link_id = lti_params.get("resource_link_id")
        resource_link_title = lti_params.get("resource_link_title")

        lti_grading_service: LTIGradingService = request.find_service(LTIGradingService)

        if not lti_grading_service.read_lineitems(
            lti_params.get("lineitems"), resource_link_id
        ):
            lineitem = lti_grading_service.create_lineitem(
                lti_params.get("lineitems"),
                resource_link_id,
                resource_link_title,
            )

            assert not lti_params.get(
                "lis_outcome_service_url"
            ), "We just created the lineitem, we expect it to be empty in the original request params"

            # This is a bit nasty, mutating the "lti_params" to fake the existence of lis_outcome_service_url
            # at the moment of the request as the rest of the code base assumes but so it's D2L behaviour.
            lti_params["lis_outcome_service_url"] = lineitem["id"]
