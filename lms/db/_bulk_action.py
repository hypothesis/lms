"""
Adds a set of low level DB operations for bulk operations.

Why is this here, rather than services?

 * The functionality is very low level and generic (we wish the basic Session
 object had it)
 * You shouldn't mock this in your code in general
 * There's nothing LMS specific about it

For more see: https://stackoverflow.com/c/hypothesis/questions/477
"""

from dataclasses import dataclass
from typing import List

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

        config = model_class.BULK_CONFIG

        stmt = insert(model_class).values(values)
        stmt = stmt.on_conflict_do_update(
            # The columns to use to find matching rows.
            index_elements=config.upsert_index_elements,
            # The columns to update.
            set_={
                element: getattr(stmt.excluded, element)
                for element in config.upsert_update_elements
            },
        )

        result = self._session.execute(stmt)

        # Let SQLAlchemy know that something has changed, otherwise it will
        # never commit the transaction we are working on and it will get rolled
        # back
        mark_changed(self._session)

        return result
