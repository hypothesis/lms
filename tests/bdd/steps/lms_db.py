"""Insert LMS specific objects into the DB."""

import contextlib

import sqlalchemy
from behave import step
from sqlalchemy.orm import sessionmaker

from lms import db, models
from tests.bdd.step_context import StepContext
from tests.conftest import TEST_DATABASE_URL


class LMSDBContext(StepContext):
    SESSION = sessionmaker()
    context_key = "db"

    def __init__(self, **kwargs):
        self.engine = sqlalchemy.create_engine(TEST_DATABASE_URL)
        self.session = None
        db.init(self.engine)
        self.do_teardown()

    def create_row(self, model_class, data):
        model_class = getattr(models, model_class)
        model = model_class(**data)

        self.session.add(model)
        self.session.commit()

    def wipe(self):
        tables = reversed(db.BASE.metadata.sorted_tables)
        with contextlib.closing(self.engine.connect()) as conn:
            tx = conn.begin()
            tnames = ", ".join('"' + t.name + '"' for t in tables)
            conn.execute("TRUNCATE {};".format(tnames))
            tx.commit()

    def do_setup(self):
        self.session = self.SESSION(bind=self.engine.connect())

    def do_teardown(self):
        self.wipe()
        if self.session:
            self.session.close()


@step("I create an LMS DB '{model_class}'")
def create_row_from_fixture(context, model_class):
    context.db.create_row(model_class, data={row[0]: row[1] for row in context.table})
