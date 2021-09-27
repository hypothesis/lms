"""Predicates for use with LTI launch views."""
from abc import ABC

from lms.views.predicates._helpers import Base


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
        ext_lti_assignment_id = request.params.get("ext_lti_assignment_id")
        tool_consumer_instance_guid = request.params.get("tool_consumer_instance_guid")

        value = (
            assignment_svc.exists(
                tool_consumer_instance_guid, resource_link_id, ext_lti_assignment_id
            )
            == self.value
        )
        return value


class IsCanvas(Base):
    """Checks if the current launch is from Canvas"""

    name = "is_canvas"

    def __call__(self, context, request):
        is_canvas = False
        if request.params.get("tool_consumer_info_product_family_code") == "canvas":
            is_canvas = True

        if "custom_canvas_course_id" in request.params:
            is_canvas = True

        return is_canvas is self.value


class IsCanvas(Base):
    """Check if the current launch comes from Canvas."""

    name = "is_canvas"

    def __call__(self, context, request):
        is_canvas = False
        if request.params.get("tool_consumer_info_product_family_code") == "canvas":
            is_canvas = True

        if "custom_canvas_course_id" in request.params:
            is_canvas = True

        return is_canvas is self.value


class _CourseCopied(Base, ABC):
    """
    Allow invoking an LTI launch view for newly course-copied assignments.

    When a user uses an LMS's Course Copy feature to copy a course that
    contains Hypothesis assignments, most (all?) LMS's copy the Hypothesis
    assignments into the new course and give the new copies of the assignments
    new resource_link_id's.

    Some LMS's then give us the resource_link_id of the original assignment as
    well, so that we can find the assignment settings in our DB when the new
    assignment is launched.

    Subclasses of this predicate allow invoking views only for newly
    course-copied assignments where we don't yet have a document_url for the
    new resource_link_id but we do have a document_url for the original
    assignment resource_link_id.
    """

    def __init__(self, value, config):
        super().__init__(value, config)
        self.db_configured = DBConfigured(True, config)

    @property
    def param_name(self):
        """
        Return the name of the launch param for the original resource_link_id.

        The name of the launch param that contains the resource_link_id of the
        original assignment that this assignment was copied from. The default
        implementation of get_original_resource_link_id() below uses this.
        """
        raise NotImplementedError()  # pragma: nocover

    @classmethod
    def get_original_resource_link_id(cls, request):
        """
        Return the original resource_link_id.

        Return the resource_link_id of the original assignment that this
        assignment was copied from.

        The default implementation uses the self.param_name property (which
        must be provided by subclasses) to retrieve a launch param.
        If the original resource_link_id can't simply be read from a launch
        param then subclasses should override get_original_resource_link_id()
        instead of overriding param_name().
        """
        return request.params.get(cls.param_name)

    def __call__(self, context, request):
        if self.db_configured(context, request):
            # We already have a document URL in the DB for this resource_link_id,
            # so it's not a newly copied assignment.
            is_newly_copied = False
        else:
            original_resource_link_id = self.get_original_resource_link_id(request)
            tool_consumer_instance_guid = request.params.get(
                "tool_consumer_instance_guid"
            )

            if not original_resource_link_id or not tool_consumer_instance_guid:
                is_newly_copied = False
            else:
                # Look for the document URL of the previous assignment that
                # this one was copied from.
                assignment_service = request.find_service(name="assignment")
                is_newly_copied = assignment_service.exists(
                    tool_consumer_instance_guid, original_resource_link_id
                )

        return is_newly_copied == self.value


class BlackboardCopied(_CourseCopied):
    """
    Allow invoking an LTI launch view for newly course-copied Blackboard assignments.

    For example:

        @view_config(..., blackboard_copied=True)
        def blackboard_course_copied_assignment_launch_view(context, request):
            ...
    """

    name = "blackboard_copied"

    # resource_link_id_history is a non-standard and undocument that's only
    # used by Blackboard as far as we know, but nothing in our code actually
    # prevents us from using resource_link_id_history if another LMS sends it
    # to us.
    param_name = "resource_link_id_history"


class BrightspaceCopied(_CourseCopied):
    """
    Allow invoking an LTI launch view for newly course-copied Brightspace assignments.

    For example:

        @view_config(..., brightspace_copied=True)
        def brightspace_course_copied_assignment_launch_view(context, request):
            ...
    """

    name = "brightspace_copied"

    # ext_d2l_resource_link_id_history is a non-standard and undocumented param
    # that's only used by Brightspace, but nothing in this code actually
    # prevents us from using ext_d2l_resource_link_id_history if another LMS
    # sends it to us.
    param_name = "ext_d2l_resource_link_id_history"


class CanvasFile(Base):
    """
    Allow invoking an LTI launch view only for Canvas file assignments.

    Newer Canvas file assignment are already present in the DB so they behave like DB Configured ones.

    Pass ``canvas_file=True`` to a view config to allow invoking the view only
    for Canvas file assignments, or ``canvas_file=False`` to allow it only for
    other types of assignment. For example::

        @view_config(..., canvas_file=True)
        def canvas_file_assignment_launch_view(context, request):
            ...
    """

    def __init__(self, value, config):
        super().__init__(value, config)
        self.db_configured = DBConfigured(True, config)

    name = "canvas_file"

    def __call__(self, context, request):
        return ("canvas_file" in request.params) == self.value and self.db_configured(
            context, request
        ) != self.value


class VitalSourceBook(Base):
    name = "vitalsource_book"

    def __call__(self, context, request):
        return ("vitalsource_book" in request.params) == self.value


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

    def __init__(self, value, config):
        super().__init__(value, config)
        self.db_configured = DBConfigured(True, config)

    def __call__(self, context, request):
        return ("url" in request.params) == self.value and self.db_configured(
            context, request
        ) != self.value


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
        self.blackboard_copied = BlackboardCopied(True, config)
        self.brightspace_copied = BrightspaceCopied(True, config)
        self.vitalsource_book = VitalSourceBook(True, config)

    def __call__(self, context, request):
        configured = any(
            [
                self.canvas_file(context, request),
                self.url_configured(context, request),
                self.db_configured(context, request),
                self.blackboard_copied(context, request),
                self.brightspace_copied(context, request),
                self.vitalsource_book(context, request),
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
