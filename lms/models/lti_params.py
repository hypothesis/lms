CLAIM_PREFIX = "https://purl.imsglobal.org/spec/lti/claim"


class LTIParams(dict):
    """
    Provides access to LTI parameters for both 1.1 and 1.3 version.

    - On 1.1, the request parameters are available both treating the object as a dict and thought the v11 property.

    - While on 1.3 the parameters from the decoded JWT are available through the v13 attribute while
    the same value are accesible using the LT1.1 names on v11 and the object's dict interface.
    """

    def __init__(self, v11: dict, v13: dict = None):
        super().__init__(v11)
        self.v13 = v13

    @property
    def v11(self):
        return self

    @classmethod
    def from_v13(cls, v13_params):
        return LTIParams(_to_lti_v11(v13_params), v13_params)


_V11_TO_V13 = (
    # LTI 1.1 key , [LTI 1.3 path in object]
    # We use tuples instead of a dictionary to allow duplicate keys for multiple locations.
    ("user_id", ["sub"]),
    ("lis_person_name_given", ["given_name"]),
    ("lis_person_name_family", ["family_name"]),
    ("lis_person_name_full", ["name"]),
    ("roles", [f"{CLAIM_PREFIX}/roles"]),
    ("context_id", [f"{CLAIM_PREFIX}/context", "id"]),
    ("context_title", [f"{CLAIM_PREFIX}/context", "title"]),
    ("lti_version", [f"{CLAIM_PREFIX}/version"]),
    ("lti_message_type", [f"{CLAIM_PREFIX}/message_type"]),
    ("resource_link_id", [f"{CLAIM_PREFIX}/resource_link", "id"]),
    # tool_consumer_instance_guid is not sent by the LTI1.3 certification tool but we include
    # it as a custom parameter in the tool configuration
    ("tool_consumer_instance_guid", [f"{CLAIM_PREFIX}/custom", "certification_guid"]),
    # Usual LTI1.3 location for tool_consumer_instance_guid
    ("tool_consumer_instance_guid", [f"{CLAIM_PREFIX}/tool_platform", "guid"]),
    (
        "tool_consumer_info_product_family_code",
        [
            f"{CLAIM_PREFIX}/tool_platform",
            "product_family_code",
        ],
    ),
)


def _to_lti_v11(v13_params):
    v11_params = {}

    for v11_key, v13_path in _V11_TO_V13:
        # Descend into the object for each item in the path
        found = False
        value = v13_params

        for path_item in v13_path:
            if path_item not in value:
                break
            value = value[path_item]
            found = True

        # We don't want to add partial values along v13_path
        if found:
            v11_params[v11_key] = value

    if "roles" in v11_params:
        # We need to squish together the roles for v1.1
        v11_params["roles"] = ",".join(v11_params["roles"])

    return v11_params
