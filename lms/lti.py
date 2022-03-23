from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class _ParamMapping:
    key: str
    """Name of the parameter in LTI1.3"""

    sub: Optional[str] = None
    """For nested values, name in the second object"""

    function: Optional[Callable] = None
    """If additional processing is needed, function to further process the value"""


def _stringify_roles(lti_13_value):
    """
    Return roles as a comma separated list of values.

    Roles are a list in LTI1.3 but comma separated in LTI1.1.
    """
    return ",".join(lti_13_value)


class LTI13Params(dict):
    """Dictionary subclass that translates LTI1.1 parameter names to the LTI1.3 ones."""

    lti_param_mapping = {
        "user_id": _ParamMapping("sub"),
        "roles": _ParamMapping(
            "https://purl.imsglobal.org/spec/lti/claim/roles", function=_stringify_roles
        ),
        "tool_consumer_instance_guid": _ParamMapping(
            "https://purl.imsglobal.org/spec/lti/claim/tool_platform", "guid"
        ),
        "tool_consumer_info_product_family_code": _ParamMapping(
            "https://purl.imsglobal.org/spec/lti/claim/tool_platform",
            "product_family_code",
        ),
        "lis_person_name_given": _ParamMapping("given_name"),
        "lis_person_name_family": _ParamMapping("family_name"),
        "lis_person_name_full": _ParamMapping("name"),
        "context_id": _ParamMapping(
            "https://purl.imsglobal.org/spec/lti/claim/context", "id"
        ),
        "context_title": _ParamMapping(
            "https://purl.imsglobal.org/spec/lti/claim/context", "title"
        ),
        "lti_version": _ParamMapping(
            "https://purl.imsglobal.org/spec/lti/claim/version"
        ),
        "lti_message_type": _ParamMapping(
            "https://purl.imsglobal.org/spec/lti/claim/message_type"
        ),
        "resource_link_id": _ParamMapping(
            "https://purl.imsglobal.org/spec/lti/claim/resource_link", "id"
        ),
        "issuer": _ParamMapping("iss"),
        "client_id": _ParamMapping("aud"),
        "deployment_id": _ParamMapping(
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id"
        ),
    }

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        """Access the LTI1.3 parameters using their corresponding LTI1.1 names."""
        if key not in self.lti_param_mapping:
            return super().__getitem__(key)

        mapping = self.lti_param_mapping[key]

        lti_13_value = super().__getitem__(mapping.key)
        if mapping.sub:
            lti_13_value = lti_13_value[mapping.sub]

        if mapping.function:
            lti_13_value = mapping.function(lti_13_value)

        return lti_13_value
