"""A helper for upserting into DB tables."""

from sqlalchemy.orm.exc import NoResultFound


def upsert(db, model_class, query_kwargs, update_kwargs):
    try:
        model = db.query(model_class).filter_by(**query_kwargs).one()
    except NoResultFound:
        model = model_class(**query_kwargs)
        db.add(model)

    for key, value in update_kwargs.items():
        setattr(model, key, value)

    return model
