import sqlalchemy as sa


def full_text_match(column, value):
    """
    Get an SQL comparator for full text matching.

    This uses a slightly janky kind of full text searching, but is more
    flexible than a direct comparison.
    """

    return sa.func.to_tsvector("english", column).op("@@")(
        sa.func.websearch_to_tsquery("english", value)
    )
