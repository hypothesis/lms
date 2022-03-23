import enum
from dataclasses import dataclass
from typing import Optional


@dataclass
class _ParamMapping:
    key: str
    sub: Optional[str] = None
    method: Optional[str] = None


class LTI13Params(dict):
    lti_param_mapping = {
        "user_id": _ParamMapping("sub"),
        "roles": _ParamMapping(
            "https://purl.imsglobal.org/spec/lti/claim/roles", method="stringify_roles"
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
            "https://purl.imsglobal.org/spec/lti/claim/context", "id"
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

    def stringify_roles(self, lti_13_value):
        return ",".join(lti_13_value)

    def get(self, key, default=None):
        try:
            return self[key] or default
        except KeyError:
            return default

    def __getitem__(self, key):
        if not key in self.lti_param_mapping:
            return super().__getitem__(key)

        mapping = self.lti_param_mapping[key]

        lti_13_value = super().__getitem__(mapping.key)
        if mapping.sub:
            lti_13_value = lti_13_value[mapping.sub]

        if mapping.method:
            lti_13_value = getattr(self, mapping.method)(lti_13_value)

        return lti_13_value
