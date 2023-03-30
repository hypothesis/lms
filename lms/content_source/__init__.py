from typing import Iterator

from lms.content_source.blackboard_files import BlackboardFiles
from lms.content_source.canvas_files import CanvasFiles
from lms.content_source.content_source import ContentSource
from lms.content_source.d2l_files.content_source import D2LFiles
from lms.content_source.google_files.content_source import GoogleFiles
from lms.content_source.jstor import JSTOR
from lms.content_source.microsoft_onedrive.content_source import MicrosoftOnedrive
from lms.content_source.models import FileDisplayConfig
from lms.content_source.vitalsource.content_source import Vitalsource


class ContentSources:
    ALL = (
        BlackboardFiles,
        CanvasFiles,
        D2LFiles,
        GoogleFiles,
        JSTOR,
        MicrosoftOnedrive,
        Vitalsource,
    )

    @classmethod
    def get_all(cls, request):
        # We shouldn't need this but the front end expects all the values
        # right now
        return (
            request.find_service(content_source_type) for content_source_type in cls.ALL
        )

    @classmethod
    def for_family(cls, request, family) -> Iterator[ContentSource]:
        for content_source_type in cls.ALL:
            # If the content source matches the family, or has no restrictions
            if content_source_type.family == family or not content_source_type.family:
                yield request.find_service(content_source_type)


def includeme(config):
    # Give everyone a chance to register
    config.include("lms.content_source.blackboard_files")
    config.include("lms.content_source.canvas_files")
    config.include("lms.content_source.d2l_files")
    config.include("lms.content_source.google_files")
    config.include("lms.content_source.jstor")
    config.include("lms.content_source.microsoft_onedrive")
    config.include("lms.content_source.vitalsource")
