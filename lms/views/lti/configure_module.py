from pyramid.view import view_config

from lms.models import ModuleItemConfiguration
from lms.validation import ConfigureModuleItemSchema
from lms.views.lti import LTIViewBaseClass


class ConfigureModuleItemView(LTIViewBaseClass):
    @view_config(
        authorized_to_configure_assignments=True,
        route_name="module_item_configurations",
        schema=ConfigureModuleItemSchema,
    )
    def configure_module_item(self):
        """
        Respond to a configure module item request.

        This happens after an unconfigured assignment launch. We show the user
        our document selection form instead of launching the assignment, and
        when the user chooses a document and submits the form this is the view
        that receives that form submission.

        We save the chosen document in the DB so that subsequent launches of
        this same assignment will be DB-configured rather than unconfigured.
        And we also send back the assignment launch page, passing the chosen
        URL to Via, as the direct response to the content item form submission.
        """
        document_url = self.request.parsed_params["document_url"]

        ModuleItemConfiguration.set_document_url(
            self.request.db,
            self.request.parsed_params["tool_consumer_instance_guid"],
            self.request.parsed_params["resource_link_id"],
            document_url,
        )

        self._set_via_url(document_url)

        return {}
