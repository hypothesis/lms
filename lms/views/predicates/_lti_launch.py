"""Predicates for use with LTI launch views."""
from lms.views.predicates._helpers import Base

__all__ = [
    "DBConfigured",
    "CanvasFile",
    "URLConfigured",
    "Configured",
    "AuthorizedToConfigureAssignments",
]


class DBConfigured(Base):
    """
    Allow invoking an LTI launch view only if the assignment is DB-configured.

    Some LTI assignments are "DB-configured" meaning the assignment's
    configuration (the URL of the document to be annotated for the assignment)
    is stored in our own DB.

    This happens with LMS's that don't support LTI "content item selection"
    (also known as "deep linking"), so they don't support storing the
    assignment configuration (document URL) in the LMS.

    Pass ``db_configured=True`` to a view's configuration to allow invoking the
    view only for requests whose assignment has its configuration stored in our
    DB. Pass ``db_configured=False`` to allow invoking the view for assignments
    that are *not* DB-configured.

    For example::

        @view_config(..., db_configured=True)
        def db_configured_assignment_launch_view(context, request):
            ...
    """

    name = "db_configured"

    def __call__(self, context, request):
        assignment_svc = request.find_service(name="assignment")
        resource_link_id = request.params.get("resource_link_id")
        tool_consumer_instance_guid = request.params.get("tool_consumer_instance_guid")

        has_document_url = bool(
            assignment_svc.get_document_url(
                tool_consumer_instance_guid, resource_link_id
            )
        )

        return has_document_url == self.value


class CanvasFile(Base):
    """
    Allow invoking an LTI launch view only for Canvas file assignments.

    Pass ``canvas_file=True`` to a view config to allow invoking the view only
    for Canvas file assignments, or ``canvas_file=False`` to allow it only for
    other types of assignment. For example::

        @view_config(..., canvas_file=True)
        def canvas_file_assignment_launch_view(context, request):
            ...
    """

    name = "canvas_file"

    def __call__(self, context, request):
        return ("canvas_file" in request.params) == self.value


class URLConfigured(Base):
    """
    Allow invoking an LTI launch view only for URL-configured assignments.

    "URL-configured" assignments are ones where the URL of the document to be
    annotated (for example a public HTML or PDF URL, or a Google Drive URL) is
    sent to us by the LMS in the ``url`` launch parameter.

    This happens when the LMS supports content-item selection (a.k.a deep
    linking) and the file to be annotated is *not* a Canvas file.

    Pass ``url_configured=True`` to a view config to allow invoking the view
    only for URL-configured assignments, or ``url_configured=False`` to allow
    it only for non-URL-configured assignments. For example::

        @view_config(..., url_configured=True)
        def url_configured_assignment_launch_view(context, request):
            ...
    """

    name = "url_configured"

    def __call__(self, context, request):
        return ("url" in request.params) == self.value


class Configured(Base):
    """
    Allow invoking an LTI launch view only if the assignment is configured.

    An *unconfigured* assignment is one for which the document URL to be
    annotated hasn't been selected yet. Regardless of whether the selected
    document URL is stored in the LMS or in our own DB, and regardless of what
    kind of file the document URL locates (HTML, Canvas PDF, Google Drive,
    ...). An unconfigured assignment is one whose document URL hasn't yet been
    chosen by any means.

    Pass ``configured=True`` to a view config to allow invoking the view only
    for assignments that're already configured, or ``configured=False`` for
    assignments that aren't yet configured. For example::

        @view_config(..., configured=True)
        def configured_assignment_launch_view(context, request):
            ...
    """

    name = "configured"

    def __init__(self, value, config):
        super().__init__(value, config)
        self.canvas_file = CanvasFile(True, config)
        self.url_configured = URLConfigured(True, config)
        self.db_configured = DBConfigured(True, config)

    def __call__(self, context, request):
        configured = any(
            [
                self.canvas_file(context, request),
                self.url_configured(context, request),
                self.db_configured(context, request),
            ]
        )
        return configured == self.value


class AuthorizedToConfigureAssignments(Base):
    """
    Allow a launch view if the user is authorized to configure assignments.

    Only certain LTI users are allowed to configure assignments (to choose the
    URL of the assignment's document). For example administrators and
    instructors are allowed to, but learners aren't.

    Pass ``authorized_to_configure_assignments=True`` to a view config to allow
    invoking the view only if the user is authorized to configure assignments.
    Pass ``authorized_to_configure_assignments=False`` to allow a view only for
    users who *aren't* so authorized.

    For example::

        @view_config(..., authorized_to_configure_assignments=True)
        def authorized_assignment_launch_view(context, request):
            ...
    """

    name = "authorized_to_configure_assignments"

    def __call__(self, context, request):
        if request.lti_user:
            roles = request.lti_user.roles.lower()
        else:
            roles = ""

        authorized = any(
            role in roles
            for role in ["administrator", "instructor", "teachingassistant"]
        )

        return authorized == self.value
