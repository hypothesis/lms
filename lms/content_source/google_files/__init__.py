from lms.content_source.google_files.content_source import GoogleFiles


def includeme(config):  # pragma: nocover
    config.register_service_factory(GoogleFiles.factory, iface=GoogleFiles)
