"""
Adds a set of low level DB operations for bulk operations.

Why is this here, rather than services?

 * The functionality is very low level and generic (we wish the basic Session
 object had it)
 * You shouldn't mock this in your code in general
 * There's nothing LMS specific about it

For more see: https://stackoverflow.com/c/hypothesis/questions/477
"""

from copy import deepcopy
from dataclasses import dataclass
from typing import List

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import insert
from zope.sqlalchemy import mark_changed


class BulkAction:
    """
    An extension to the DB session which adds bulk actions.

    These can be accessed via request.db.bulk.<method_name>().

    To enable for a particular model add config to the model like this:

        class MyModel(BASE):
            # Enable bulk actions
            BULK_CONFIG = BulkAction.Config(
                upsert_index_elements=[...],
                upsert_update_elements=[...],
            )
    """

    def __init__(self, session):
        """
        Initialize object.

        :session: SQLAlchemy session object
        """
        self._session = session

    @dataclass
    class Config:
        upsert_index_elements: List[str]
        """Columns to match when upserting. This must match an index."""

        upsert_update_elements: List[str]
        """Columns to update when a match is found."""

        upsert_trigger_onupdate: bool = True
        """Column to update with the current datetime"""

        def __set_name__(self, owner, name):
            if name != "BULK_CONFIG":
                raise ValueError(
                    "The configuration must be attached to the model with "
                    "the name 'BULK_CONFIG'"
                )

    def upsert(self, model_class, values):
        """
        Create or update the specified values in the table.

        :param model_class: The model type to upsert
        :param values: Dicts of values to upsert
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

        config = model_class.BULK_CONFIG

        upsert_update_elements = list(config.upsert_update_elements)

        if config.upsert_trigger_onupdate:
            onupdate_columns = self._get_columns_onupdate(model_class)

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
            index_elements=config.upsert_index_elements,
            # The columns to update.
            set_={
                element: getattr(stmt.excluded, element)
                for element in upsert_update_elements
            },
        )

        result = self._session.execute(stmt)

        # Let SQLAlchemy know that something has changed, otherwise it will
        # never commit the transaction we are working on and it will get rolled
        # back
        mark_changed(self._session)

        return result

    @staticmethod
    def _get_columns_onupdate(model_class):
        """Get which columns which have an onupdate clause and its value."""
        model_details = inspect(model_class)

        return [(c.name, c.onupdate.arg) for c in model_details.c if c.onupdate]
