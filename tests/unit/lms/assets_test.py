from lms.assets import includeme


def test_includeme(pyramid_config):
    includeme(pyramid_config)

    assets_env = pyramid_config.registry["assets_env"]
    assert assets_env.assets_base_url == "/assets"
