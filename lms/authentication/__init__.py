from pyramid.authentication import AuthTktAuthenticationPolicy

from lms.security import groupfinder


__all__ = ()


def includeme(config):
    config.set_authentication_policy(
        AuthTktAuthenticationPolicy(
            config.registry.settings["lms_secret"],
            callback=groupfinder,
            hashalg="sha512",
        )
    )
