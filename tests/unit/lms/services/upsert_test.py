import sqlalchemy as sa
from h_matchers import Any

from lms.db import BASE
from lms.services.upsert import bulk_upsert


class TestBulkAction:
    INDEX_ELEMENTS = ["id"]
    UPDATE_COLUMNS = ["name"]

    class TableWithBulkUpsert(BASE):
        __tablename__ = "test_table_with_bulk_upsert"

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

        result = bulk_upsert(
            db_session,
            self.TableWithBulkUpsert,
            [
                {"id": 1, "name": "update_old", "other": "post_1"},
                {"id": 3, "name": "create_with_id", "other": "post_3"},
                {"id": 4, "name": "over_block_size", "other": "post_4"},
            ],
            self.INDEX_ELEMENTS,
            self.UPDATE_COLUMNS,
        )

        expected_rows = [
            {"id": 1, "name": "update_old", "other": "pre_1"},
            {"id": 2, "name": "pre_existing_2", "other": "pre_2"},
            {"id": 3, "name": "create_with_id", "other": "post_3"},
            {"id": 4, "name": "over_block_size", "other": "post_4"},
        ]

        # Upsert has made the expected changes in the DB
        self.assert_has_rows(db_session, *expected_rows)

        # Also returned the affected rows
        for model in result:
            assert {
                "id": model.id,
                "name": model.name,
                "other": model.other,
            } in expected_rows

    def test_upsert_return_empty_query_if_given_an_empty_list_of_values(
        self, db_session
    ):
        assert (
            bulk_upsert(
                db_session,
                self.TableWithBulkUpsert,
                [],
                self.INDEX_ELEMENTS,
                self.UPDATE_COLUMNS,
            ).all()
            == []
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
