from pyramid.view import view_config
from lms.models.module_item_configuration import ModuleItemConfiguration
from lms.util.authenticate import authenticate


@view_config(
    route_name="module_item_configurations",
    renderer="lms:templates/lti_launches/new_lti_launch.html.jinja2",
    request_method="POST",
)
@authenticate
def create_module_item_configuration(request, _jwt, **_):
    instance = ModuleItemConfiguration(
        document_url=request.params["document_url"],
        resource_link_id=request.params["resource_link_id"],
        tool_consumer_instance_guid=request.params["tool_consumer_instance_guid"],
    )

    request.db.add(instance)
    return {
        "hypothesis_url": f"{request.registry.settings['via_url']}/{instance.document_url}",
        "jwt_token": request.params["jwt_token"],
    }
