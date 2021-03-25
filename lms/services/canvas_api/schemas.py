from enum import Enum
from marshmallow import EXCLUDE, Schema, fields, post_load, validate, validates_schema
from lms.validation import RequestsResponseSchema


class ListGroups(RequestsResponseSchema):

    many = True

    id = fields.Integer(required=True)

    name = fields.Str(required=True)
    description = fields.String(default=None, allow_none=True)
    group_category_id = fields.Integer(required=True)


class ListGroupCategories(RequestsResponseSchema):

    many = True

    id = fields.Integer(required=True)

    name = fields.Str(required=True)
    description = fields.String(default=None, allow_none=True)

    role = fields.Str(required=False, allow_none=True)
    content_type = fields.Str(required=False, allow_none=True)


class MembershipState(Enum):
    ACCEPTED = "accepted"
    INVITED = "invited"
    REQUESTED = "requested"


class ListGroupMemberships(RequestsResponseSchema):

    many = True

    id = fields.Integer(required=True)
    group_id = fields.Integer(required=True)
    user_id = fields.Integer(required=True)
    workflow_state = fields.Str(required=True)


class Profile(RequestsResponseSchema):
    id = fields.Integer(required=True)
    name = fields.Str(required=True)
    short_name = fields.Str(required=True)
    lti_user_id = fields.Str(required=False, allow_none=True)
    sis_user_id = fields.Str(required=False, allow_none=True)
    login_id = fields.Str(required=False, allow_none=True)
    primary_email = fields.Str(required=False, allow_none=True)
