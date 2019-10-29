import pyramid_tm

from lms.config import configure


def configure_jinja2_assets(config):
    jinja2_env = config.get_jinja2_environment()
    jinja2_env.globals["asset_url"] = config.registry["assets_env"].url
    jinja2_env.globals["asset_urls"] = config.registry["assets_env"].urls


def create_app(global_config, **settings):  # pylint: disable=unused-argument
    config = configure(settings=settings)

    # Make sure that pyramid_exclog's tween runs under pyramid_tm's tween so
    # that pyramid_exclog doesn't re-open the DB session after pyramid_tm has
    # already closed it.
    config.add_tween(
        "pyramid_exclog.exclog_tween_factory", under="pyramid_tm.tm_tween_factory"
    )
    config.add_settings({"exclog.extra_info": True})
    config.include("pyramid_exclog")

    config.include("pyramid_jinja2")
    config.include("pyramid_services")

    # Use pyramid_tm's explicit transaction manager.
    #
    # This means that trying to access a request's transaction after pyramid_tm
    # has closed the request's transaction will crash, rather than implicitly
    # opening a new transaction that doesn't get closed (and potentially
    # leaking open DB connections).
    #
    # This is recommended in the pyramid_tm docs:
    #
    # https://docs.pylonsproject.org/projects/pyramid_tm/en/latest/#custom-transaction-managers
    config.registry.settings["tm.manager_hook"] = pyramid_tm.explicit_manager

    config.include("pyramid_tm")

    config.include("lms.authentication")
    config.include("lms.extensions.feature_flags")
    config.add_feature_flag_providers(
        "lms.extensions.feature_flags.config_file_provider",
        "lms.extensions.feature_flags.envvar_provider",
        "lms.extensions.feature_flags.cookie_provider",
        "lms.extensions.feature_flags.query_string_provider",
    )

    config.include("lms.sentry")
    config.include("lms.session")
    config.include("lms.models")
    config.include("lms.db")
    config.include("lms.routes")
    config.include("lms.assets")
    config.include("lms.views")
    config.include("lms.views.error")
    config.include("lms.services")
    config.include("lms.validation")
    config.add_static_view(name="export", path="lms:static/export")
    config.add_static_view(name="static", path="lms:static")

    config.registry.settings["jinja2.filters"] = {
        "static_path": "pyramid_jinja2.filters:static_path_filter",
        "static_url": "pyramid_jinja2.filters:static_url_filter",
    }

    config.action(None, configure_jinja2_assets, args=(config,))

    config.scan()

    return config.make_wsgi_app()
