from dataclasses import dataclass

from pyramid.events import subscriber
from pyramid.request import Request

from lms.models import Event, EventType, LtiLaunches
from lms.services import EventService, LTIRoleService


@dataclass
class LTILaunchEvent:
    request: Request


@dataclass
class LTIDeepLinkingEvent:
    request: Request
    document_url: str


@subscriber(LTILaunchEvent)
def handle_lti_launch_event(event: LTILaunchEvent):
    request = event.request

    # Record Launch in the legacy LtiLaunches table
    LtiLaunches.add(
        request.db,
        request.lti_params.get("context_id"),
        request.lti_params.get("oauth_consumer_key"),
    )

    # Record the launch as en event in the Event model's table
    request.find_service(EventService).insert_event(
        type_=EventType.Type.CONFIGURED_LAUNCH,
        user=request.user,
        lti_roles=request.find_service(LTIRoleService).get_roles(
            request.lti_params["roles"]
        ),
        application_instance=request.find_service(
            name="application_instance"
        ).get_current(),
        course=request.find_service(name="course").get_by_context_id(
            request.lti_params["context_id"]
        ),
        assignment=request.find_service(name="assignment").get_assignment(
            request.lti_params["tool_consumer_instance_guid"],
            request.lti_params["resource_link_id"],
        ),
    )


@subscriber(LTIDeepLinkingEvent)
def handle_deep_linking_event(event: LTIDeepLinkingEvent):
    request = event.request

    request.find_service(EventService).insert_event(
        type_=EventType.Type.DEEP_LINKING,
        user=request.user,
        application_instance=request.find_service(
            name="application_instance"
        ).get_current(),
        course=request.find_service(name="course").get_by_context_id(
            request.json["context_id"]
        ),
        data={"document_url": event.document_url},
    )


def includeme(config):  # pragma: no cover
    config.scan(__name__)
