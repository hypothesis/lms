import pytest
from sqlalchemy.exc import IntegrityError

from lms.models import Assignment, AutoGradingConfig
from tests import factories


class TestAssignment:
    def test_set_canvas_mapped_file_id_creates_a_new_mapping_if_none_exists(
        self, assignment
    ):
        assignment.set_canvas_mapped_file_id("original_file_id", "mapped_file_id")

        assert (
            assignment.get_canvas_mapped_file_id("original_file_id") == "mapped_file_id"
        )

    def test_set_canvas_mapped_file_id_overwrites_an_existing_mapping_if_one_exists(
        self, assignment
    ):
        assignment.set_canvas_mapped_file_id("original_file_id", "mapped_file_id")

        assignment.set_canvas_mapped_file_id("original_file_id", "new_mapped_file_id")

        assert (
            assignment.get_canvas_mapped_file_id("original_file_id")
            == "new_mapped_file_id"
        )

    def test_get_canvas_mapped_file_id_returns_the_given_file_id_if_no_mapping_exists(
        self, assignment
    ):
        assert assignment.get_canvas_mapped_file_id("file_id") == "file_id"

    @pytest.fixture
    def assignment(self, db_session):
        assignment = Assignment(
            resource_link_id="resource_link_id",
            tool_consumer_instance_guid="tool_consumer_instance_guid",
            document_url="document_url",
        )
        db_session.add(assignment)
        db_session.flush()
        return assignment


class TestAutoGradingConfig:
    def test_configs_form_a_chain(self, db_session):
        first, second = factories.AutoGradingConfig.create_batch(2)
        db_session.flush()

        second.previous_config = first
        db_session.flush()

        assert second.previous_config_id == first.id
        assert second.previous_config == first

    def test_the_first_config_of_a_chain_has_no_previous_config(self, db_session):
        config = factories.AutoGradingConfig()
        db_session.flush()

        assert config.previous_config_id is None
        assert config.previous_config is None

    def test_every_assignment_can_have_a_config_with_no_previous_config(
        self, db_session
    ):
        # The unique constraint must leave NULLs distinct: each assignment's
        # first config has previous_config_id NULL.
        factories.AutoGradingConfig.create_batch(2)

        db_session.flush()

    def test_a_config_cannot_be_the_previous_config_of_two_others(self, db_session):
        first, second, third = factories.AutoGradingConfig.create_batch(3)
        db_session.flush()
        second.previous_config = first
        db_session.flush()

        third.previous_config = first

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_deleting_a_config_deletes_the_rest_of_the_chain(self, db_session):
        first, second = factories.AutoGradingConfig.create_batch(2)
        db_session.flush()
        second.previous_config = first
        db_session.flush()

        db_session.delete(first)
        db_session.flush()

        assert not db_session.query(AutoGradingConfig).count()

    @pytest.mark.parametrize(
        (
            "activity_calculation",
            "required_annotations",
            "required_replies",
            "expected",
        ),
        [
            ("cumulative", 3, None, True),
            ("cumulative", 0, None, False),
            # A cumulative config only counts its combined goal, so a replies
            # goal left over from a separate one asks for nothing.
            ("cumulative", 0, 3, False),
            ("separate", 3, 0, True),
            ("separate", 0, 3, True),
            ("separate", 0, 0, False),
            ("separate", 0, None, False),
        ],
    )
    def test_requires_activity(
        self, activity_calculation, required_annotations, required_replies, expected
    ):
        config = AutoGradingConfig(
            activity_calculation=activity_calculation,
            grading_type="scaled",
            required_annotations=required_annotations,
            required_replies=required_replies,
        )

        assert config.requires_activity == expected
