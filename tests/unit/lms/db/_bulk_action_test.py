import pytest
import sqlalchemy as sa
from h_matchers import Any
from sqlalchemy.engine import CursorResult

from lms.db import BASE, BulkAction


class TestBulkAction:
    class TableWithBulkUpsert(BASE):
        __tablename__ = "test_table_with_bulk_upsert"

        BULK_CONFIG = BulkAction.Config(
            upsert_index_elements=["id"],
            upsert_update_elements=["name"],
            upsert_trigger_onupdate=False,
        )

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String, nullable=False)
        other = sa.Column(sa.String)

        # Lots of auto update columns
        scalar = sa.Column(sa.Integer, onupdate=42)
        callable = sa.Column(sa.Integer, onupdate=lambda: 42)
        sql = sa.Column(sa.Integer, onupdate=sa.select([42]))
        default = sa.Column(sa.Integer, sa.schema.ColumnDefault(42, for_update=True))

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

        self.assert_has_rows(
            db_session,
            {"id": 1, "name": "update_old", "other": "pre_1"},
            {"id": 2, "name": "pre_existing_2", "other": "pre_2"},
            {"id": 3, "name": "create_with_id", "other": "post_3"},
            {"id": 4, "name": "over_block_size", "other": "post_4"},
        )

    def test_upsert_does_nothing_if_given_an_empty_list_of_values(self, db_session):
        assert BulkAction(db_session).upsert(self.TableWithBulkUpsert, []) == []

    @pytest.mark.parametrize("column", ("scalar", "callable", "sql", "default"))
    @pytest.mark.usefixtures("with_upsert_trigger_onupdate")
    def test_upsert_with_onupdate_columns(self, db_session, column):
        db_session.add_all(
            [
                self.TableWithBulkUpsert(id=1, name="pre_existing_1", **{column: 0}),
                self.TableWithBulkUpsert(id=2, name="pre_existing_2", **{column: 1}),
            ]
        )
        db_session.flush()

        BulkAction(db_session).upsert(
            self.TableWithBulkUpsert, [{"id": 1, "name": "update_existing"}]
        )

        self.assert_has_rows(
            db_session,
            # 42 is the onupdate default value
            {"id": 1, "name": "update_existing", column: 42},
            {"id": 2, "name": "pre_existing_2", column: 1},
        )

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

    def assert_has_rows(self, db_session, *attrs):
        rows = list(db_session.query(self.TableWithBulkUpsert))

        assert (
            rows
            == Any.iterable.containing(
                [
                    Any.instance_of(self.TableWithBulkUpsert).with_attrs(expected)
                    for expected in attrs
                ]
            ).only()
        )

    @pytest.fixture
    def with_upsert_trigger_onupdate(self):
        self.TableWithBulkUpsert.BULK_CONFIG.upsert_trigger_onupdate = True
        yield
        self.TableWithBulkUpsert.BULK_CONFIG.upsert_trigger_onupdate = False
