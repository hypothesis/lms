from lms.content_source.content_source import ContentSource
from lms.content_source.google_files.content_source import GoogleFiles
from lms.content_source.jstor import JSTOR
from lms.content_source.microsoft_onedrive.content_source import MicrosoftOnedrive
from lms.content_source.models import FileDisplayConfig
from lms.content_source.vitalsource.content_source import Vitalsource

DEFAULT_CONTENT_SOURCES = (GoogleFiles, JSTOR, MicrosoftOnedrive, Vitalsource)


def includeme(config):
    # Give everyone a chance to register
    config.include("lms.content_source.google_files")
    config.include("lms.content_source.jstor")
    config.include("lms.content_source.microsoft_onedrive")
    config.include("lms.content_source.vitalsource")
