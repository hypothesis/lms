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
        if not self.settings.auto_create_lineitem:
            if lti_params["lti_version"] != "1.3.0":
                # D2L doesn't automatically create a line item for assignments by default like it does for 1.1.
                # If we are creating them automatically in our end all of them will be gradable.
                return True

        return super().is_gradable(lti_params)

    def ltia_aud_claim(self, _lti_registration):
        # In D2L this value is always the same
        return "https://api.brightspace.com/auth/token"

    def configure_assignment(self, request):
        if not self.settings.auto_create_lineitem:
            return

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
            # We could now do something like:
            #   lti_params["lis_outcome_service_url"] = lineitem["id"]
            # to align the lti_params and the lineitem we just created.
            # This is not necessary as we only creating the lineitem on assignment configuration,
            # when we know we won't have any student submissions.
            # The next launches will have the right value in `lis_outcome_service_url`
