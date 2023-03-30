from lms.content_source.blackboard_files.content_source import BlackboardFiles


def includeme(config):  # pragma: nocover
    config.register_service_factory(BlackboardFiles.factory, iface=BlackboardFiles)
