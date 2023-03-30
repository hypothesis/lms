from lms.content_source.vitalsource.content_source import Vitalsource


def includeme(config):  # pragma: nocover
    config.register_service_factory(Vitalsource.factory, iface=Vitalsource)
