import logging
from datetime import datetime

from dateutil import parser

CLAIM_PREFIX = "https://purl.imsglobal.org/spec/lti/claim"

LOG = logging.getLogger(__name__)


class LTIParams(dict):
    """
    Provides access to LTI parameters for both 1.1 and 1.3 version.

    On 1.1, the request parameters are available both treating the object as
    a dict and thought the v11 property.

    While on 1.3, the parameters from the decoded JWT are available through the
    v13 attribute while the same value are accessible using the LT1.1 names on
    v11 and the object's dict interface.
    """

    def __init__(self, v11: dict, v13: dict | None = None):
        super().__init__(v11)
        # Always have a dictionary in v13. Avoids a None comparison to callers
        self.v13 = v13 if v13 else {}

    @property
    def v11(self):
        return self

    def get_datetime(self, key: str) -> datetime | None:
        """Get a datetime from the LTI parameters."""
        try:
            return parser.isoparse(self.get(key))
        except (TypeError, ValueError):
            return None

    @classmethod
    def from_request(cls, request):
        """Create an LTIParams from the request."""

        if v13_params := request.lti_jwt:
            v11, v13 = _to_lti_v11(v13_params), v13_params
        elif request.content_type == "application/json":
            v11, v13 = request.json_body, None
        else:
            v11, v13 = request.params, None

        lti_params = cls(v11=v11, v13=v13)

        # This would be good if we could extract this as a product plugin (or
        # something similar), but unfortunately there's currently a circular
        # dependency where LTI params are required to get the product
        lti_params = _apply_canvas_quirks(lti_params, request)

        return lti_params

    def serialize(self, **kwargs) -> dict:
        """
        Serialize LTIParams to be sent over the wire.

        The serialized version will look like the 1.1 version of the
        LTI parameters excluding any authorization related fields.

        :param kwargs: Additional fields to add to the output.
        """
        form_fields = {
            param: value
            for param, value in self.items()
            # Don't send over auth related params. We'll use our own
            # authorization
            if param
            not in {"oauth_nonce", "oauth_timestamp", "oauth_signature", "id_token"}
            |
            # We also don't want to include parameters that are not part of the LTI spec
            # but we might submit together in a form while creating and editing assigments.
            {"auto_grading_config"}
        }
        form_fields.update(**kwargs)
        return form_fields


def _apply_canvas_quirks(lti_params, request):
    # Canvas SpeedGrader launches LTI apps with the wrong resource_link_id,
    # see:
    # * https://github.com/instructure/canvas-lms/issues/1952
    # * https://github.com/hypothesis/lms/issues/3228
    #
    # We add the correct resource_link_id as a query param on the launch
    # URL that we submit to Canvas and use that instead of the incorrect
    # resource_link_id that Canvas puts in the request's body.

    # This is canvas only, call the right plugin directly
    # Importing the plugin here to avoid a circular dependency hell
    from lms.product.canvas._plugin.misc import (
        CanvasMiscPlugin,
    )

    is_speedgrader = CanvasMiscPlugin().is_speed_grader_launch(request)

    if is_speedgrader and (resource_link_id := request.GET.get("resource_link_id")):
        lti_params["resource_link_id"] = resource_link_id

    for canvas_param_name in ["custom_canvas_course_id", "custom_canvas_user_id"]:
        # In LTI1.3 some custom canvas parameters were sent as integers
        # and as strings in LTI1.1.
        # With this update:
        #   https://community.canvaslms.com/t5/Canvas-Change-Log/Canvas-Platform-Breaking-Changes/ta-p/262015
        # They should also be strings in LTI1.3 but not all
        # canvas instances run the last version so we are keeping this for some time
        canvas_param_value = lti_params.get(canvas_param_name)
        if isinstance(canvas_param_value, int):
            LOG.debug("Canvas: integer value for %s", canvas_param_name)
            lti_params[canvas_param_name] = str(canvas_param_value)

    return lti_params


_V11_TO_V13 = (
    # LTI 1.1 key , [LTI 1.3 path in object]
    # We use tuples instead of a dictionary to allow duplicate keys for multiple locations.
    ("user_id", ["sub"]),
    # In case we want to access the LTI1.3 value directly using the version independent dict access
    ("sub", ["sub"]),
    ("lis_person_name_given", ["given_name"]),
    ("lis_person_name_family", ["family_name"]),
    ("lis_person_name_full", ["name"]),
    # Middle name is LTI1.3 only
    ("middle_name", ["middle_name"]),
    ("lis_person_contact_email_primary", ["email"]),
    ("roles", [f"{CLAIM_PREFIX}/roles"]),
    ("context_id", [f"{CLAIM_PREFIX}/context", "id"]),
    ("context_title", [f"{CLAIM_PREFIX}/context", "title"]),
    ("lti_version", [f"{CLAIM_PREFIX}/version"]),
    ("lti_message_type", [f"{CLAIM_PREFIX}/message_type"]),
    ("resource_link_id", [f"{CLAIM_PREFIX}/resource_link", "id"]),
    ("resource_link_title", [f"{CLAIM_PREFIX}/resource_link", "title"]),
    ("resource_link_description", [f"{CLAIM_PREFIX}/resource_link", "description"]),
    # tool_consumer_instance_guid is not sent by the LTI1.3 certification tool but we include
    # it as a custom parameter in the tool configuration
    ("tool_consumer_instance_guid", [f"{CLAIM_PREFIX}/custom", "certification_guid"]),
    # Usual LTI1.3 location for tool_consumer_instance_guid
    ("tool_consumer_instance_guid", [f"{CLAIM_PREFIX}/tool_platform", "guid"]),
    (
        "tool_consumer_info_product_family_code",
        [f"{CLAIM_PREFIX}/tool_platform", "product_family_code"],
    ),
    (
        "tool_consumer_instance_contact_email",
        [f"{CLAIM_PREFIX}/tool_platform", "contact_email"],
    ),
    (
        "tool_consumer_instance_name",
        [f"{CLAIM_PREFIX}/tool_platform", "name"],
    ),
    (
        "tool_consumer_instance_description",
        [f"{CLAIM_PREFIX}/tool_platform", "description"],
    ),
    (
        "tool_consumer_instance_url",
        [f"{CLAIM_PREFIX}/tool_platform", "url"],
    ),
    (
        "tool_consumer_info_version",
        [f"{CLAIM_PREFIX}/tool_platform", "version"],
    ),
    (
        "lis_outcome_service_url",
        ["https://purl.imsglobal.org/spec/lti-ags/claim/endpoint", "lineitem"],
    ),
    (
        "lineitems",
        ["https://purl.imsglobal.org/spec/lti-ags/claim/endpoint", "lineitems"],
    ),
    ("lis_result_sourcedid", ["sub"]),
    (
        "content_item_return_url",
        [
            "https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings",
            "deep_link_return_url",
        ],
    ),
    (
        "lis_person_sourcedid",
        [f"{CLAIM_PREFIX}/lis", "person_sourcedid"],
    ),
    (
        "deep_linking_settings",
        ["https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings"],
    ),
    # Some LMSs provide a https://purl.imsglobal.org/spec/lti/claim/lti1p1 claim
    # with the LTI1.1 version value of some IDs that are different in LTI1.3.
    # To make upgrades seamless we prefer the LTI1.1 version when available
    #
    # http://www.imsglobal.org/spec/lti/v1p3/migr#lti-1-1-migration-claim
    ("user_id", [f"{CLAIM_PREFIX}/lti1p1", "user_id"]),
    ("resource_link_id", [f"{CLAIM_PREFIX}/lti1p1", "resource_link_id"]),
    # LMS dependant variables that are not part of the "custom" claim
    ("org_defined_id", ["http://www.brightspace.com", "org_defined_id"]),
)


def _to_lti_v11(v13_params):
    v11_params = {}

    for v11_key, v13_path in _V11_TO_V13:
        try:
            v11_params[v11_key] = _get_key(v13_params, v13_path)
        except KeyError:
            # We don't want to add partial values along v13_path
            continue

    # Deal with the custom params. See:
    # https://www.imsglobal.org/spec/lti/v1p3/#custom-properties-and-variable-substitution
    if custom := v13_params.get(f"{CLAIM_PREFIX}/custom"):
        v11_params.update({f"custom_{key}": value for key, value in custom.items()})

    if "roles" in v11_params:
        # We need to squish together the roles for v1.1 compatibility
        v11_params["roles"] = ",".join(v11_params["roles"])

    return v11_params


def _get_key(data: dict, data_path: list[str]):
    # Descend into the object for each item in the path
    value = data
    for path_item in data_path:
        value = value[path_item]

    return value


def includeme(config):
    config.add_request_method(
        LTIParams.from_request, name="lti_params", property=True, reify=True
    )
