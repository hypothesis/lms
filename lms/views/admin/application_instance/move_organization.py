from pyramid.view import view_config

from lms.security import Permissions
from lms.validation import ValidationError
from lms.views.admin.application_instance._core import BaseApplicationInstanceView


class MoveOrgApplicationInstanceView(BaseApplicationInstanceView):
    @view_config(
        route_name="admin.instance.move_org",
        request_method="POST",
        require_csrf=True,
        permission=Permissions.ADMIN,
    )
    def move_application_instance_org(self):
        ai = self.application_instance

        try:
            self.application_instance_service.update_application_instance(
                ai,
                organization_public_id=self.request.params.get(
                    "org_public_id", ""
                ).strip(),
            )
            self.request.session.flash(
                f"Updated application instance {ai.id}", "messages"
            )
        except ValidationError as err:
            self.request.session.flash(err.messages, "validation")

        return self._redirect("admin.instance", id_=ai.id)
