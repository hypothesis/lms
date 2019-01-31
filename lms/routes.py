# -*- coding: utf-8 -*-
from lms.config.resources import LTILaunch


def includeme(config):
    config.add_route("index", "/")
    config.add_route("welcome", "/welcome")
    config.add_route("login", "/login")
    config.add_route("logout", "/logout")
    config.add_route("reports", "/reports")
    config.add_route("config_xml", "/config_xml")
    config.add_route(
        "module_item_configurations", "/module_item_configurations", factory=LTILaunch
    )
    config.add_route("canvas_proxy", "/canvas_proxy")

    # lms routes
    config.add_route("lti_launches", "/lti_launches", factory=LTILaunch)
    config.add_route(
        "content_item_selection", "/content_item_selection", factory=LTILaunch
    )

    # Oauth
    config.add_route("canvas_oauth_callback", "/canvas_oauth_callback")
    config.add_route(
        "module_item_launch_oauth_callback",
        "/module_item_launch_oauth_callback",
        factory=LTILaunch,
    )

    # Assets
    config.add_route("assets", "/assets/*subpath")

    # Health check endpoint for load balancers to request.
    config.add_route("status", "/_status")

    # Make requests to /favicon.ico work.
    # Browsers seem to send requests to this URL on their own accord, even
    # though we dont link to it.
    config.add_route("favicon", "/favicon.ico")
