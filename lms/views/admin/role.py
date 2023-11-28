from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults

from lms.events import AuditTrailEvent
from lms.security import Permissions
from lms.services.application_instance import ApplicationInstanceService
from lms.services.lti_role_service import LTIRoleService


@view_defaults(permission=Permissions.ADMIN)
class AdminRoleViews:
    def __init__(self, request):
        self.request = request
        self.application_instance_service: ApplicationInstanceService = (
            request.find_service(name="application_instance")
        )
        self.lti_role_service = request.find_service(LTIRoleService)

    @view_config(
        route_name="admin.role.override.new",
        request_method="GET",
        renderer="lms:templates/admin/role.override.new.html.jinja2",
    )
    def new_override(self):
        instance = self.application_instance_service.get_by_id(
            id_=self.request.matchdict["id_"]
        )
        existing_roles = [
            (role.id, role.value) for role in self.lti_role_service.search()
        ]

        return {"instance": instance, "existing_roles": existing_roles}

    @view_config(route_name="admin.role.override.new", request_method="POST")
    def new_override_post(self):
        instance = self.application_instance_service.get_by_id(
            id_=self.request.matchdict["id_"]
        )
        role = self.lti_role_service.search(id_=self.request.params["role_id"]).one()

        override = self.lti_role_service.new_role_override(
            instance, role, self.request.params["type"], self.request.params["scope"]
        )
        AuditTrailEvent.notify(self.request, override)
        self.request.session.flash(
            f"Created new role override for {role.value}", "messages"
        )

        return HTTPFound(
            location=self.request.route_url("admin.instance", id_=instance.id)
        )

    @view_config(
        route_name="admin.role.override",
        request_method="GET",
        renderer="lms:templates/admin/role.override.html.jinja2",
    )
    def show(self):
        override = self.lti_role_service.search_override(
            id_=self.request.matchdict["id_"]
        ).one()
        existing_roles = [
            (role.id, role.value) for role in self.lti_role_service.search()
        ]

        return {
            "override": override,
            "existing_roles": existing_roles,
        }

    @view_config(route_name="admin.role.override", request_method="POST")
    def update(self):
        override = self.lti_role_service.search_override(
            id_=self.request.matchdict["id_"]
        ).one()

        self.lti_role_service.update_override(
            override,
            scope=self.request.params["scope"],
            type_=self.request.params["type"],
        )

        AuditTrailEvent.notify(self.request, override)
        self.request.session.flash(
            f"Updated role override for {override.value}", "messages"
        )
        return HTTPFound(
            location=self.request.route_url("admin.role.override", id_=override.id)
        )

    @view_config(route_name="admin.role.override.delete", request_method="POST")
    def delete(self):
        override = self.lti_role_service.search_override(
            id_=self.request.matchdict["id_"]
        ).one()

        self.lti_role_service.delete_override(override)
        AuditTrailEvent.notify(self.request, override)
        self.request.session.flash(
            f"Deleted role override for {override.value}", "messages"
        )

        return HTTPFound(
            location=self.request.route_url(
                "admin.instance", id_=override.application_instance_id
            )
        )
