import sqlalchemy as sa
from marshmallow import fields
from marshmallow.validate import Equal
from pyramid.exceptions import HTTPForbidden
from pyramid.view import view_config

from lms.models import Assignment, AssignmentMembership, Grouping, ReusedConsumerKey
from lms.security import Permissions
from lms.validation import LTIV11CoreSchema


class GatewayLTISchema(LTIV11CoreSchema):
    location = "form"

    # Specify the context (either assignment or whole course level)
    context_id = fields.Str(required=True)
    context_title = fields.Str(required=True)
    resource_link_id = fields.Str()

    # We don't need these exactly, but it proves the caller is sending us a
    # well-formed LTI request. It also limits us to 1.1, because this whole
    # approach doesn't really work with 1.3 at the moment.
    lti_version = fields.Str(validate=Equal("LTI-1p0"), required=True)
    lti_message_type = fields.Str(
        validate=Equal("basic-lti-launch-request"),
        required=True,
    )


class GatewayViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @view_config(
        request_method="POST",
        permission=Permissions.API,
        renderer="json",
        route_name="api.gateway.h.lti",
        schema=GatewayLTISchema,
    )
    def h_lti(self):
        """
        Provide tokens and information to allow customers to query H.

        We expect the user to authenticate with us using an LTI launch.
        """
        self._ensure_guid_aligns()

        # Before the credentials we provide will be accepted by `h` the user must
        # exist. So we'll sync over the details to `h`. We also put the user in the
        # course group. This means they will see annotations at the course level
        # right away. If the course uses groups or sections, they won't see
        # anything until they launch an assignment and get put in a group.
        self.request.find_service(name="lti_h").sync(
            [self.context.course], self.request.lti_params
        )

        return {
            "api": {"h": _GatewayService.render_h_connection_info(self.request)},
            "data": _GatewayService.render_lti_context(self.request),
        }

    def _ensure_guid_aligns(self):
        # Ensure no funny business is going on trying to access content out of the
        # current application instance scope.
        try:
            self.context.application_instance.check_guid_aligns(
                self.request.lti_params["tool_consumer_instance_guid"]
            )
        except ReusedConsumerKey as err:
            raise HTTPForbidden(
                "Claimed `tool_consumer_instance_guid` does not match credentials."
            ) from err


class _GatewayService:
    @classmethod
    def render_h_connection_info(cls, request):
        h_api_url = request.registry.settings["h_api_url_public"]

        return {
            # These sections are arranged so you can use
            # `requests.Request.request(**data)` and make the correct request
            "list_endpoints": {
                # List the API end-points
                "method": "GET",
                "url": h_api_url,
                "headers": {"Accept": "application/vnd.hypothesis.v2+json"},
            },
            "exchange_grant_token": {
                # Exchange our token for access and refresh tokens
                "method": "POST",
                "url": h_api_url + "token",
                "headers": {
                    "Accept": "application/vnd.hypothesis.v2+json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                "data": {
                    # Generate a short-lived login token for the Hypothesis client
                    "assertion": request.find_service(
                        name="grant_token"
                    ).generate_token(request.lti_user.h_user),
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                },
            },
        }

    @classmethod
    def render_lti_context(cls, request):
        assignments = cls._get_assignments_from_lti(request)
        h_user = request.lti_user.h_user
        authority = request.registry.settings["h_authority"]

        return {
            # This might be of interest to our consumers, but mostly this is
            # for out own debugging if they have trouble. They can give us the
            # whole response, and we'll get a lot of useful info
            "parameters": {"1.1": request.lti_params.v11},
            "assignments": [
                {
                    # The document is required so the user can tie annotations
                    # back to the document they relate to
                    "lms": {
                        "document_url": assignment.document_url,
                    },
                    "lti": {
                        "resource_link_id": assignment.resource_link_id,
                        "resource_link_title": assignment.title,
                        "resource_link_description": assignment.description,
                    },
                    # Dump groupings in relation to this assignment
                    "groups": [
                        cls._render_grouping(grouping, authority)
                        for grouping in assignment.groupings
                    ],
                    # Dump users for the assignment. This is required as the
                    # roles are only relative to the assignment. So a user can
                    # be one role in this assignment and a different role in
                    # another
                    "users": cls._render_assignment_users(assignment),
                }
                for assignment in assignments
            ],
            # Details of the current user
            "profile": {
                "userid": h_user.userid(authority),
                "display_name": h_user.display_name,
                "lti": {
                    "user_id": h_user.provider_unique_id,
                },
            },
        }

    @classmethod
    def _get_assignments_from_lti(cls, request):
        assignment_svc = _AssignmentService(request.db)

        resource_link_id = request.lti_params.get("resource_link_id")
        if not resource_link_id:
            course = request.find_service(name="course").get_by_context_id(
                request.lti_params["context_id"]
            )
            return assignment_svc.get_assignments_for_course(course.id)

        if assignment := assignment_svc.get_assignment(
            tool_consumer_instance_guid=request.lti_params[
                "tool_consumer_instance_guid"
            ],
            resource_link_id=request.lti_params.get("resource_link_id"),
        ):
            return [assignment]

        return []

    @staticmethod
    def _render_grouping(grouping, authority):
        return {
            "groupid": grouping.groupid(authority),
            "name": grouping.name,
            # In the general case groups can't really have an "LTI" section
            # becacuse they can come from all over the place.
            "lms": {
                "id": grouping.lms_id,
                "parentId": grouping.parent.lms_id if grouping.parent else None,
                "type": grouping.type,
            },
        }

    @staticmethod
    def _render_assignment_users(assignment):
        roles_by_user = {}
        for membership in assignment.user_memberships:
            roles_by_user.setdefault(membership.user, [])
            roles_by_user[membership.user].append(membership.lti_role)

        return [
            {
                "userid": user.h_userid,
                "lti": {
                    "user_id": user.user_id,
                    # Convert to the standard roles string
                    "roles": ",".join(lti_role.value for lti_role in lti_roles),
                },
                "lms": {
                    "roles": [
                        {
                            "value": lti_role.value,
                            "type": lti_role.type,
                        }
                        for lti_role in lti_roles
                    ]
                },
            }
            for user, lti_roles in roles_by_user.items()
        ]


class _AssignmentService:
    def __init__(self, db):
        self._db = db

    def get_assignments_for_course(self, course_id):
        query = self._db.query(Assignment)
        query = self._eager_load_groupings(query, Grouping.id == course_id)
        query = self._eager_load_users(query)
        return query.all()

    def get_assignment(
        self, tool_consumer_instance_guid, resource_link_id, eager_load=False
    ) -> Assignment:
        """Get an assignment by resource_link_id."""

        query = self._db.query(Assignment).filter_by(
            tool_consumer_instance_guid=tool_consumer_instance_guid,
            resource_link_id=resource_link_id,
        )
        if eager_load:
            query = self._eager_load_groupings(query)
            query = self._eager_load_users(query)

        return query.one_or_none()

    @staticmethod
    def _eager_load_groupings(query, grouping_join=None):
        return query.options(
            sa.orm.subqueryload(Assignment.groupings, grouping_join).options(
                sa.orm.subqueryload(Grouping.parent)
            )
        )

    @staticmethod
    def _eager_load_users(query):
        return query.options(
            sa.orm.subqueryload(Assignment.user_memberships).options(
                sa.orm.joinedload(AssignmentMembership.user),
                sa.orm.joinedload(AssignmentMembership.lti_role),
            )
        )
