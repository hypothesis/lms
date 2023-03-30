from lms.content_source.models import FileDisplayConfig


class ContentSource:
    config_key: str = None
    url_scheme: str = None

    # pylint: disable=unused-argument
    def is_enabled(self, application_instance) -> bool:
        """Is this content source enabled?"""

        return True

    # pylint: disable=unused-argument
    def get_picker_config(self, application_instance) -> dict:
        """Get the configuration required for the file picker."""

        return {}

    def get_file_display_config(self, document_url) -> FileDisplayConfig:
        """
        Get the configuration to display a given document URL.

        This should only be called if the document URL matches the specified
        `url_scheme`, so you can assume it's relevant.
        """

        assert False, "If we've got here something is wrong."
