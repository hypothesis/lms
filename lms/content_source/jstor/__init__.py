from lms.content_source.jstor.content_source import JSTOR


def includeme(config):  # pragma: nocover
    config.register_service_factory(JSTOR.factory, iface=JSTOR)
