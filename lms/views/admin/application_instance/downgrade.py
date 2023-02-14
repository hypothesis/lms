from pyramid.view import view_config

from lms.security import Permissions
from lms.views.admin.application_instance._core import BaseApplicationInstanceView


class DowngradeApplicationInstanceView(BaseApplicationInstanceView):
    @view_config(
        route_name="admin.instance.downgrade",
        request_method="POST",
        permission=Permissions.ADMIN,
    )
    def downgrade_instance(self):
        ai = self.application_instance

        if ai.lti_version != "1.3.0":
            self.request.session.flash(
                f"Application instance: '{ai.id}' is not on LTI 1.3.", "errors"
            )
        elif not ai.consumer_key:
            self.request.session.flash(
                f"Application instance: '{ai.id}' doesn't have a consumer key to fallback to.",
                "errors",
            )
        else:
            ai.lti_registration_id = None
            ai.deployment_id = None

            self.request.session.flash("Downgraded LTI 1.1 successful", "messages")

        return self._redirect("admin.instance", id_=ai.id)
