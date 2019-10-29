import pyramid_retry
import pyramid_tm
from sqlalchemy.exc import IntegrityError

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
    config.include("pyramid_retry")

    # Mark all sqlalchemy IntegrityError's as retryable.
    #
    # This means that if any request fails with any IntegrityError error then
    # pyramid_retry will re-try the request up to two times. No error response
    # will be sent back to the client, and no crash reported to Sentry, unless
    # the request fails three times in a row (or one of the re-tries fails with
    # a non-retryable error).
    #
    # This does mean that if a request is failing with a non-transient
    # IntegrityError (so the request has no hope of succeeding on retry) then
    # we will pointlessly retry the request twice before failing.
    #
    # But we shouldn't have too many non-transient IntegrityError's anyway
    # (sounds like a bug) and marking all IntegrityError's as retryable means
    # that in all cases when an IntegrityError *is* transient and the request
    # *can* succeed on retry, it will be retried, without having to mark those
    # IntegrityErrors as retryable on a case-by-case basis.
    #
    # Examples of transient/retryable IntegrityError's are when doing either
    # upsert or create-if-not-exists logic when entering rows into the DB:
    # concurrent requests can both see that the DB row doesn't exist yet and
    # try to create the DB row at the same time and one of them will fail. If
    # retried the failed request will now see that the DB row already exists
    # and not try to create it, and the request will succeed.
    pyramid_retry.mark_error_retryable(IntegrityError)

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
    config.include("lms.tweens")
    config.add_static_view(name="export", path="lms:static/export")
    config.add_static_view(name="static", path="lms:static")

    config.registry.settings["jinja2.filters"] = {
        "static_path": "pyramid_jinja2.filters:static_path_filter",
        "static_url": "pyramid_jinja2.filters:static_url_filter",
    }

    config.action(None, configure_jinja2_assets, args=(config,))

    config.scan()

    return config.make_wsgi_app()
