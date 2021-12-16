"""A helper for upserting into DB tables."""

from copy import deepcopy
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import inspect, column
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import or_, and_, tuple_
from zope.sqlalchemy import mark_changed


def upsert(db, model_class, query_kwargs, update_kwargs):
    try:
        model = db.query(model_class).filter_by(**query_kwargs).one()
    except NoResultFound:
        model = model_class(**query_kwargs)
        db.add(model)

    for key, value in update_kwargs.items():
        setattr(model, key, value)

    return model


def bulk_orm_upsert(db, models, search_columns, update_columns):
    def _search_criteria_values(model, search_columns):
        return {column: getattr(model, column.key) for column in search_columns}

    if not models:
        return []

    ModelsClass = models[0].__class__
    assert all((model.__class__ == ModelsClass for model in models))

    search_criteria = []
    existing_models_by_search = {}
    for model in models:
        model_search_criteria = _search_criteria_values(model, search_columns)
        model_search_values = tuple(model_search_criteria.values())

        # Build a lookup dict from the value of the search column to the model
        existing_models_by_search[model_search_values] = model

        # For every model we have to "and" the search columns
        search_criteria.append(
            and_(*[column == value for column, value in model_search_criteria.items()])
        )

    # Aggregate all search criteria in a big "or" to find all existing columns
    db_models = db.query(ModelsClass).filter(or_(*search_criteria)).all()

    for db_model in db_models:
        model_search_criteria = _search_criteria_values(db_model, search_columns)
        model_search_values = tuple(model_search_criteria.values())

        # For every existing model, update the necessary columns finding the original model in the lookup dict
        update_model = existing_models_by_search[model_search_values]
        for update_column in update_columns:
            setattr(
                db_model,
                update_column.key,
                getattr(update_model, update_column.key),
            )

        del existing_models_by_search[model_search_values]

    # We deleted models from the lookup dict as we went through the existing ones.
    # The only ones left are the ones that need an insert.
    (db.add(model) for model in existing_models_by_search)

    return list(existing_models_by_search.values()) + db_models


def bulk_upsert(
    db, ModelsClass, values, index_elements, update_columns, use_on_update=True
):
    """
    Create or update the specified values in the table.

    :param model_class: The model type to upsert
    :param values: Dicts of values to upsert
    """

    def _get_columns_onupdate(model_class):
        """Get which columns which have an onupdate clause and its value."""
        model_details = inspect(model_class)

        return [(c.name, c.onupdate.arg) for c in model_details.c if c.onupdate]

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

    if use_on_update:
        onupdate_columns = _get_columns_onupdate(ModelsClass)

        for column_name, onupdate_value in onupdate_columns:
            update_columns.append(column_name)

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

    index_elements_columns = [column(c) for c in index_elements]

    stmt = insert(ModelsClass).values(values)
    stmt = stmt.on_conflict_do_update(
        # The columns to use to find matching rows.
        index_elements=index_elements,
        # The columns to update.
        set_={element: getattr(stmt.excluded, element) for element in update_columns},
    ).returning(*index_elements_columns)

    result = db.execute(stmt).all()

    # Let SQLAlchemy know that something has changed, otherwise it will
    # never commit the transaction we are working on and it will get rolled
    # back
    mark_changed(db)

    # Return ORM objects based on index_elements
    return (
        db.query(ModelsClass).filter(tuple_(*index_elements_columns).in_(result)).all()
    )
