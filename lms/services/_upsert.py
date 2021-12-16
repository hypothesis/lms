"""A helper for upserting into DB tables."""

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import or_, and_


def upsert(db, model_class, query_kwargs, update_kwargs):
    try:
        model = db.query(model_class).filter_by(**query_kwargs).one()
    except NoResultFound:
        model = model_class(**query_kwargs)
        db.add(model)

    for key, value in update_kwargs.items():
        setattr(model, key, value)

    return model


def bulk_upsert(db, models, search_columns, update_columns):
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

        # For every existing model, update the neccessary columns finding the original model in the lookup dict
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
