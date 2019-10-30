__all__ = ["upsert_group_info"]


def upsert_group_info(context, request):
    """Create or update the GroupInfo for the given request."""
    request.find_service(name="group_info_upsert")(
        context.h_authority_provided_id,
        request.lti_user.oauth_consumer_key,
        **{
            param: request.params.get(param)
            for param in [
                "context_id",
                "context_title",
                "context_label",
                "tool_consumer_info_product_family_code",
                "tool_consumer_info_version",
                "tool_consumer_instance_name",
                "tool_consumer_instance_description",
                "tool_consumer_instance_url",
                "tool_consumer_instance_contact_email",
                "tool_consumer_instance_guid",
                "custom_canvas_api_domain",
                "custom_canvas_course_id",
            ]
        },
    )
