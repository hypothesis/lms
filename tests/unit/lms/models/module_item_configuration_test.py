import pytest

from lms.models import ModuleItemConfiguration


class TestModuleItemConfiguration:
    def test_set_canvas_mapped_file_id_creates_a_new_mapping_if_none_exists(self, mic):
        mic.set_canvas_mapped_file_id("original_file_id", "mapped_file_id")

        assert mic.get_canvas_mapped_file_id("original_file_id") == "mapped_file_id"

    def test_set_canvas_mapped_file_id_overwrites_an_existing_mapping_if_one_exists(
        self, mic
    ):
        mic.set_canvas_mapped_file_id("original_file_id", "mapped_file_id")

        mic.set_canvas_mapped_file_id("original_file_id", "new_mapped_file_id")

        assert mic.get_canvas_mapped_file_id("original_file_id") == "new_mapped_file_id"

    def test_get_canvas_mapped_file_id_returns_the_given_file_id_if_no_mapping_exists(
        self, mic
    ):
        assert mic.get_canvas_mapped_file_id("file_id") == "file_id"

    @pytest.fixture
    def mic(self, db_session):
        mic = ModuleItemConfiguration(
            resource_link_id="resource_link_id",
            tool_consumer_instance_guid="tool_consumer_instance_guid",
            document_url="document_url",
        )
        db_session.add(mic)
        db_session.flush()
        return mic
