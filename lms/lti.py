CLAIM_PREFIX = "https://purl.imsglobal.org/spec/lti/claim"
V11_TO_V13 = {
    # LTI 1.1 key -> [LTI 1.3 path in object]
    "user_id": ["sub"],
    "lis_person_name_given": ["given_name"],
    "lis_person_name_family": ["family_name"],
    "lis_person_name_full": ["name"],
    "roles": [f"{CLAIM_PREFIX}/roles"],
    "context_id": [f"{CLAIM_PREFIX}/context", "id"],
    "context_title": [f"{CLAIM_PREFIX}/context", "title"],
    "lti_version": [f"{CLAIM_PREFIX}/version"],
    "lti_message_type": [f"{CLAIM_PREFIX}/message_type"],
    "resource_link_id": [f"{CLAIM_PREFIX}/resource_link", "id"],
    "tool_consumer_instance_guid": [f"{CLAIM_PREFIX}/tool_platform", "guid"],
    "tool_consumer_info_product_family_code": [
        f"{CLAIM_PREFIX}/tool_platform",
        "product_family_code",
    ],
}


def to_lti_v11(v13_params):
    v11_params = {}

    for v11_key, v13_path in V11_TO_V13.items():
        # Descend into the object for each item in the path
        value = v13_params
        if v13_path[0] not in v13_params:
            continue

        for path_item in v13_path:
            value = value[path_item]

        v11_params[v11_key] = value

    if "roles" in v11_params:
        # We need to squish together the roles for v1.1
        v11_params["roles"] = ",".join(v11_params["roles"])

    return v11_params
