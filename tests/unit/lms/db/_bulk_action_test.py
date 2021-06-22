import pytest
import sqlalchemy as sa
from h_matchers import Any
from sqlalchemy.engine import CursorResult

from lms.db import BASE, BulkAction


class TestBulkAction:
    class TableWithBulkUpsert(BASE):
        __tablename__ = "test_table_with_bulk_upsert"

        BULK_CONFIG = BulkAction.Config(
            upsert_index_elements=["id"], upsert_update_elements=["name"]
        )

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String, nullable=False)
        other = sa.Column(sa.String)

    def test_upsert(self, db_session):
        db_session.add_all(
            [
                self.TableWithBulkUpsert(id=1, name="pre_existing_1", other="pre_1"),
                self.TableWithBulkUpsert(id=2, name="pre_existing_2", other="pre_2"),
            ]
        )
        db_session.flush()

        result = BulkAction(db_session).upsert(
            self.TableWithBulkUpsert,
            [
                {"id": 1, "name": "update_old", "other": "post_1"},
                {"id": 3, "name": "create_with_id", "other": "post_3"},
                {"id": 4, "name": "over_block_size", "other": "post_4"},
            ],
        )

        assert isinstance(result, CursorResult)

        rows = list(db_session.query(self.TableWithBulkUpsert))

        assert (
            rows
            == Any.iterable.containing(
                [
                    Any.instance_of(self.TableWithBulkUpsert).with_attrs(expected)
                    for expected in [
                        {"id": 1, "name": "update_old", "other": "pre_1"},
                        {"id": 2, "name": "pre_existing_2", "other": "pre_2"},
                        {"id": 3, "name": "create_with_id", "other": "post_3"},
                        {"id": 4, "name": "over_block_size", "other": "post_4"},
                    ]
                ]
            ).only()
        )

    def test_upsert_does_nothing_if_given_an_empty_list_of_values(self, db_session):
        assert BulkAction(db_session).upsert(self.TableWithBulkUpsert, []) == []

    def test_it_fails_with_missing_config(self, db_session):
        with pytest.raises(AttributeError):
            BulkAction(db_session).upsert(
                "object_without_config", [{"id": 1, "name": "name", "other": "other"}]
            )

    def test_you_cannot_add_config_with_the_wrong_name(self):
        # Not sure why this isn't ValueError... must be a descriptor thing
        with pytest.raises(RuntimeError):

            class MisconfiguredModel:  # pylint: disable=unused-variable
                NOT_THE_RIGHT_NAME = BulkAction.Config(
                    upsert_index_elements=["id"], upsert_update_elements=["name"]
                )
