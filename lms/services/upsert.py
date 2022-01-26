"""A helper for upserting into DB tables."""

from typing import List

from sqlalchemy import column, tuple_
from sqlalchemy.dialects.postgresql import insert
from zope.sqlalchemy import mark_changed


def bulk_upsert(
    db,
    model_class,
    values: List[dict],
    index_elements: List[str],
    update_columns: List[str],
):
    """
    Create or update the specified values in a table.

    :param db: An SQLAlchemy session
    :param model_class: The model type to upsert
    :param values: Dicts of values to upsert
    :param index_elements: Columns to match when upserting. This must match an index.
    :param update_columns: Columns to update when a match is found.
    :return: A lazy query of the affected `model_class` rows.
    """
    if not values:
        # Don't attempt to upsert an empty list of values into the DB.
        #
        # This would be worse than pointless: it would actually crash in
        # some cases. This SQLAlchemy code:
        #
        #     insert(MyModel).values([])
        #
        # produces this SQL:
        #
        #     INSERT INTO my_table DEFAULT VALUES RETURNING my_table.id
        #
        # which tells the DB to insert one row into my_table using the
        # default values for all of the columns. If my_table has a column
        # with a NOT NULLABLE constraint and no default value this will
        # cause a "null value violates not-null constraint" crash.
        return []

    index_elements_columns = [column(c) for c in index_elements]

    stmt = insert(model_class).values(values)
    stmt = stmt.on_conflict_do_update(
        # The columns to use to find matching rows.
        index_elements=index_elements,
        # The columns to update.
        set_={element: getattr(stmt.excluded, element) for element in update_columns},
    ).returning(*index_elements_columns)

    result = db.execute(stmt)

    # Let SQLAlchemy know that something has changed, otherwise it will
    # never commit the transaction we are working on and it will get rolled
    # back
    mark_changed(db)

    return db.query(model_class).filter(
        tuple_(*index_elements_columns).in_(result.all())
    )
