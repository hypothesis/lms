"""
Pyramid event subscribers.

See https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/events.html
"""


__all__ = []


def includeme(config):
    config.scan(__name__)
