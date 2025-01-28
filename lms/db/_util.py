from sqlalchemy import Select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Query


def compile_query(query: Query | Select, literal_binds: bool = True) -> str:  # noqa: FBT001, FBT002
    """
    Return the SQL representation of `query` for postgres.

    :param literal_binds: Whether or not replace the query parameters by their values.
    """
    if isinstance(query, Query):  # noqa: SIM108
        # Support for SQLAlchemy 1.X style queryies, eg: db.query(Model).filter_by()
        statement = query.statement
    else:
        # SQLALchemy 2.X style, eg: select(Model).where()
        statement = query

    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": literal_binds},
        )
    )
