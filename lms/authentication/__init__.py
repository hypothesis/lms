from lms.authentication._policy import AuthenticationPolicy


__all__ = ()


def includeme(config):
    config.include("lms.authentication._helpers")
    config.set_authentication_policy(
        AuthenticationPolicy(config.registry.settings["lms_secret"])
    )
