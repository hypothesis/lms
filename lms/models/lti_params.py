from typing import Iterable, List

CLAIM_PREFIX = "https://purl.imsglobal.org/spec/lti/claim"


class LTIParams(dict):
    """
    Provides access to LTI parameters for both 1.1 and 1.3 version.

    On 1.1, the request parameters are available both treating the object as
    a dict and thought the v11 property.

    While on 1.3, the parameters from the decoded JWT are available through the
    v13 attribute while the same value are accessible using the LT1.1 names on
    v11 and the object's dict interface.
    """

    def __init__(self, v11: dict, v13: dict = None):
        super().__init__(v11)
        self.v13 = v13

    @property
    def v11(self):
        return self

    @classmethod
    def from_request(cls, request):
        """Create an LTIParams from the request."""

        plugin: LTIParamPlugin = request.product.plugin.lti_param

        if v13_params := request.lti_jwt:
            v11, v13 = _to_lti_v11(v13_params, plugin.v13_parameter_map), v13_params
        else:
            v11, v13 = request.params, None

        lti_params = cls(v11=v11, v13=v13)
        return plugin.modify_params(lti_params, request)


class LTIParamPlugin:
    """An interface for allowing products to customise parameter loading."""

    v13_parameter_map: Iterable = (
        # LTI 1.1 key , [LTI 1.3 path in object]
        # We use tuples instead of a dictionary to allow duplicate keys for
        # multiple locations.
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
        ("resource_link_title", [f"{CLAIM_PREFIX}/resource_link", "title"]),
        ("resource_link_description", [f"{CLAIM_PREFIX}/resource_link", "description"]),
        # tool_consumer_instance_guid is not sent by the LTI1.3 certification
        # tool but we include it as a custom parameter in the tool configuration
        (
            "tool_consumer_instance_guid",
            [f"{CLAIM_PREFIX}/custom", "certification_guid"],
        ),
        # Usual LTI1.3 location for tool_consumer_instance_guid
        ("tool_consumer_instance_guid", [f"{CLAIM_PREFIX}/tool_platform", "guid"]),
        (
            "tool_consumer_info_product_family_code",
            [f"{CLAIM_PREFIX}/tool_platform", "product_family_code"],
        ),
        (
            "lis_outcome_service_url",
            ["https://purl.imsglobal.org/spec/lti-ags/claim/endpoint", "lineitem"],
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
            "deep_linking_settings",
            ["https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings"],
        ),
        # Some LMSs provide a https://purl.imsglobal.org/spec/lti/claim/lti1p1
        # claim with the LTI1.1 version value of some IDs that are different in
        # LTI1.3. To make upgrades seamless we prefer the LTI1.1 version when
        # available
        #
        # http://www.imsglobal.org/spec/lti/v1p3/migr#lti-1-1-migration-claim
        ("user_id", [f"{CLAIM_PREFIX}/lti1p1", "user_id"]),
        ("resource_link_id", [f"{CLAIM_PREFIX}/lti1p1", "resource_link_id"]),
    )

    # pylint: disable=unused-argument
    @classmethod
    def modify_params(cls, lti_params: LTIParams, request) -> LTIParams:
        """
        Modify the LTI params that were passed in.

        This can be done in any way but must return a child of LTIParams.
        """
        return lti_params

    @classmethod
    def from_request(cls, request):  # pylint: disable=unused-argument
        return cls()


def _to_lti_v11(v13_params, param_mapping):
    v11_params = {}

    for v11_key, v13_path in param_mapping:
        try:
            v11_params[v11_key] = _get_key(v13_params, v13_path)
        except KeyError:
            # We don't want to add partial values along v13_path
            continue

    if "roles" in v11_params:
        # We need to squish together the roles for v1.1
        v11_params["roles"] = ",".join(v11_params["roles"])

    return v11_params


def _get_key(data: dict, data_path: List[str]):
    # Descend into the object for each item in the path
    value = data
    for path_item in data_path:
        value = value[path_item]

    return value


def includeme(config):
    config.add_request_method(
        LTIParams.from_request, name="lti_params", property=True, reify=True
    )
