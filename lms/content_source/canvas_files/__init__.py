from lms.content_source.canvas_files.content_source import CanvasFiles


def includeme(config):  # pragma: nocover
    config.register_service_factory(CanvasFiles.factory, iface=CanvasFiles)
