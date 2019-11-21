import contextlib

import sqlalchemy
from behave import step
from sqlalchemy.orm import sessionmaker

from lms import db, models
from tests.conftest import TEST_DATABASE_URL


class LMSDBContext:
    SESSION = sessionmaker()

    def __init__(self):
        self.engine = sqlalchemy.create_engine(TEST_DATABASE_URL)
        self.session = None
        db.init(self.engine)

    def teardown(self):
        tables = reversed(db.BASE.metadata.sorted_tables)
        with contextlib.closing(self.engine.connect()) as conn:
            tx = conn.begin()
            tnames = ", ".join('"' + t.name + '"' for t in tables)
            conn.execute("TRUNCATE {};".format(tnames))
            tx.commit()

        self.session.close()

    def setup(self):
        self.session = self.SESSION(bind=self.engine.connect())

    @classmethod
    def register(cls, context):
        context.db = LMSDBContext()

        return context.db


@step("I create an LMS DB '{model_class}'")
def create_row_from_fixture(context, model_class):
    print(model_class)
    model_class = getattr(models, model_class)
    data = {row[0]: row[1] for row in context.table}
    model = model_class(**data)

    session = context.db.session
    session.add(model)
    session.commit()
