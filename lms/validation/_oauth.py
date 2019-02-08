"""Validation for OAuth views."""
from webargs import fields


#: Arguments for the canvas_oauth_callback() view.
CANVAS_OAUTH_CALLBACK_SCHEMA = {
    "code": fields.Str(required=True),
    "state": fields.Str(required=True),
}
