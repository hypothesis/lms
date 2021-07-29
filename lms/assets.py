"""View for serving static assets under `/assets`."""

import importlib_resources
from h_assets import Environment, assets_view


def includeme(config):
    # Auto reload asset manifest when it changes in development.
    auto_reload = config.registry.settings["dev"]
    lms_files = importlib_resources.files("lms")

    assets_env = Environment(
        assets_base_url="/assets",
        bundle_config_path=lms_files / "assets.ini",
        manifest_path=lms_files / "../build/manifest.json",
        auto_reload=auto_reload,
    )

    # Store asset environment in registry for use in registering `asset_urls`
    # Jinja2 helper in `app.py`.
    config.registry["assets_env"] = assets_env

    config.add_view(route_name="assets", view=assets_view(assets_env))
