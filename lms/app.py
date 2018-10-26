import logging
from lms.config import configure

log = logging.getLogger(__name__)


def configure_jinja2_assets(config):
    jinja2_env = config.get_jinja2_environment()
    jinja2_env.globals['asset_url'] = config.registry['assets_env'].url
    jinja2_env.globals['asset_urls'] = config.registry['assets_env'].urls


def create_app(global_config, **settings):  # pylint: disable=unused-argument
    config = configure(settings=settings)

    config.include('pyramid_jinja2')
    config.include('pyramid_tm')
    config.include('pyramid_exclog')

    config.include('lms.sentry')
    config.include('lms.models')
    config.include('lms.db')
    config.include('lms.routes')
    config.include('lms.assets')
    config.add_static_view(name='export', path='lms:static/export')
    config.add_static_view(name='static', path='lms:static')

    config.registry.settings['jinja2.filters'] = {
        'static_path': 'pyramid_jinja2.filters:static_path_filter',
        'static_url': 'pyramid_jinja2.filters:static_url_filter',
    }

    config.action(None, configure_jinja2_assets, args=(config,))

    config.scan()

    return config.make_wsgi_app()
