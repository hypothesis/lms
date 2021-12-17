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

        upsert_use_onupdate: bool = True
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
        config = model_class.BULK_CONFIG

        from lms.services._upsert import (  # pylint:disable=import-outside-toplevel
            bulk_upsert,
        )

        return bulk_upsert(
            self._session,
            model_class,
            values,
            config.upsert_index_elements,
            config.upsert_update_elements,
            config.upsert_use_onupdate,
        )
