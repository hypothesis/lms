from lms.content_source.d2l_files.content_source import D2LFiles


def includeme(config):  # pragma: nocover
    config.register_service_factory(D2LFiles.factory, iface=D2LFiles)
