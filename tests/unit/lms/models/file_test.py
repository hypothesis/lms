from tests import factories


def test_store_big_size_file(db_session):
    file = factories.File()
    file.size = 2_147_483_647 + 1000  # Too big for pg's integer type
    db_session.add(file)

    db_session.commit()

    assert file.size > 2_147_483_647
