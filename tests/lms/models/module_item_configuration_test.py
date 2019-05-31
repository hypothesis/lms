import pytest

from lms.models import ModuleItemConfiguration


class TestModuleItemConfiguration:
    def test_get_document_url_returns_the_document_url(self, db_session):
        db_session.add(
            ModuleItemConfiguration(
                tool_consumer_instance_guid="test_tool_consumer_instance_guid",
                resource_link_id="test_resource_link_id",
                document_url="test_document_url",
            )
        )

        document_url = ModuleItemConfiguration.get_document_url(
            db_session, "test_tool_consumer_instance_guid", "test_resource_link_id"
        )

        assert document_url == "test_document_url"

    def test_get_document_url_returns_None_if_theres_no_matching_document_url(
        self, db_session
    ):
        document_url = ModuleItemConfiguration.get_document_url(
            db_session, "test_tool_consumer_instance_guid", "test_resource_link_id"
        )

        assert document_url is None

    def test_set_document_url_saves_the_document_url(self, db_session):
        ModuleItemConfiguration.set_document_url(
            db_session,
            "test_tool_consumer_instance_guid",
            "test_resource_link_id",
            "NEW_DOCUMENT_URL",
        )

        assert (
            db_session.query(ModuleItemConfiguration)
            .filter_by(
                tool_consumer_instance_guid="test_tool_consumer_instance_guid",
                resource_link_id="test_resource_link_id",
            )
            .one()
            .document_url
            == "NEW_DOCUMENT_URL"
        )

    def test_set_document_url_overwrites_an_existing_document_url(self, db_session):
        db_session.add(
            ModuleItemConfiguration(
                tool_consumer_instance_guid="test_tool_consumer_instance_guid",
                resource_link_id="test_resource_link_id",
                document_url="OLD_DOCUMENT_URL",
            )
        )

        ModuleItemConfiguration.set_document_url(
            db_session,
            "test_tool_consumer_instance_guid",
            "test_resource_link_id",
            "NEW_DOCUMENT_URL",
        )

        assert (
            db_session.query(ModuleItemConfiguration)
            .filter_by(
                tool_consumer_instance_guid="test_tool_consumer_instance_guid",
                resource_link_id="test_resource_link_id",
            )
            .one()
            .document_url
            == "NEW_DOCUMENT_URL"
        )

    @pytest.fixture(autouse=True)
    def noise(self, db_session):
        db_session.add_all(
            [
                ModuleItemConfiguration(
                    tool_consumer_instance_guid="noise_tool_consumer_instance_guid_1",
                    resource_link_id="noise_resource_link_id_1",
                    document_url="noise_document_url_1",
                ),
                ModuleItemConfiguration(
                    tool_consumer_instance_guid="noise_tool_consumer_instance_guid_2",
                    resource_link_id="noise_resource_link_id_2",
                    document_url="noise_document_url_2",
                ),
                ModuleItemConfiguration(
                    tool_consumer_instance_guid="noise_tool_consumer_instance_guid_3",
                    resource_link_id="noise_resource_link_id_3",
                    document_url="noise_document_url_3",
                ),
            ]
        )
