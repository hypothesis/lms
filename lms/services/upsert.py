"""A helper for upserting into DB tables."""

from typing import List
from copy import deepcopy

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import inspect
from zope.sqlalchemy import mark_changed


def bulk_upsert(  # pylint:disable=too-many-arguments
    db,
    model_class,
    values: List[dict],
    index_elements: List[str],
    update_columns: List[str],
    use_onupdate=False,
):
    """
    Create or update the specified values in the table.
    :param db: An SQLAlchemy session
    :param model_class: The model type to upsert
    :param values: Dicts of values to upsert
    :param index_elements: Columns to match when upserting. This must match an index.
    :param update_columns: Columns to update when a match is found.
    :param use_onupdate: Update columns defined with onupdte on the ORM model.
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

    upsert_update_elements = list(update_columns)

    if use_onupdate:
        onupdate_columns = _get_columns_onupdate(model_class)

        for column_name, onupdate_value in onupdate_columns:
            upsert_update_elements.append(column_name)

            # SQL alchemy wraps functions passed to onupdate or default and
            # could potentially take a "context" argument getting a
            # suitable context at this point of the execution it's not
            # possible so we don't support it so we just pass None
            # https://docs.sqlalchemy.org/en/14/core/defaults.html#context-sensitive-default-functions
            default_value = (
                onupdate_value(None) if callable(onupdate_value) else onupdate_value
            )

            # Copy the values, we don't want to mess with the caller's data
            values = deepcopy(values)
            for row in values:
                row[column_name] = default_value

    stmt = insert(model_class).values(values)
    stmt = stmt.on_conflict_do_update(
        # The columns to use to find matching rows.
        index_elements=index_elements,
        # The columns to update.
        set_={
            element: getattr(stmt.excluded, element)
            for element in upsert_update_elements
        },
    )

    result = db.execute(stmt)

    # Let SQLAlchemy know that something has changed, otherwise it will
    # never commit the transaction we are working on and it will get rolled
    # back
    mark_changed(db)

    return result


def _get_columns_onupdate(model_class):
    """Get which columns which have an onupdate clause and its value."""
    model_details = inspect(model_class)

    return [(c.name, c.onupdate.arg) for c in model_details.c if c.onupdate]
