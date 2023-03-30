from lms.content_source.microsoft_onedrive.content_source import MicrosoftOnedrive


def includeme(config):  # pragma: nocover
    config.register_service_factory(MicrosoftOnedrive.factory, iface=MicrosoftOnedrive)
