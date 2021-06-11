from dataclasses import dataclass
from typing import List

from sqlalchemy.dialects.postgresql import insert
from zope.sqlalchemy import mark_changed

from lms.db._session_extension import SessionExtension


class BulkAction(SessionExtension):
    """
    An extension to the DB session which adds bulk actions.

    These can be accessed via `session.bulk.<method_name>()`.

    To enable for a particular model add config to the model like this:

        class MyModel(BASE):
            # Enable bulk actions
            BULK_CONFIG = BulkAction.Config(
                upsert_index_elements=[...],
                upsert_update_elements=[...],
            )
    """

    @dataclass
    class Config:
        upsert_index_elements: List[str]
        """Columns to match when upserting. This must match an index."""

        upsert_update_elements: List[str]
        """Columns to update when a match is found."""

        def __set_name__(self, owner, name):
            # Ensure we have the right name when attached to objects
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

        config = self._get_config(model_class)

        stmt = insert(model_class).values(values)
        stmt = stmt.on_conflict_do_update(
            # Match when the rules are the same
            index_elements=config.upsert_index_elements,
            # Then set these elements
            set_={
                element: getattr(stmt.excluded, element)
                for element in config.upsert_update_elements
            },
        )

        # This session attribute is here because we are a session extension
        result = self.session.execute(stmt)

        # Let SQLAlchemy know that something has changed, otherwise it will
        # never commit the transaction we are working on and it will get rolled
        # back
        mark_changed(self.session)

        return result

    @classmethod
    def _get_config(cls, model_class):
        """
        Get the bulk config in this model or raise.

        :param model_class: Class to get config from
        :rtype: Config
        :raises NotImplementedError: If the config is missing
        """
        try:
            return model_class.BULK_CONFIG
        except AttributeError as err:
            raise NotImplementedError(
                f"Model class '{model_class}' does not have the expected config "
                "attribute: 'BULK_CONFIG'"
            ) from err
