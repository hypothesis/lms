import contextlib

import sqlalchemy


from lms import db
from lms.app import create_app
from tests.conftest import TEST_SETTINGS, TEST_DATABASE_URL
from tests.bdd.steps import TheFixture, TheRequest, OAuth1Context, TheApp


TEST_SETTINGS["session_cookie_secret"] = "notasecret"


class DBContext:
    def __init__(self):
        self.engine = sqlalchemy.create_engine(TEST_DATABASE_URL)
        db.init(self.engine)

    def teardown(self):
        tables = reversed(db.BASE.metadata.sorted_tables)
        with contextlib.closing(self.engine.connect()) as conn:
            tx = conn.begin()
            tnames = ", ".join('"' + t.name + '"' for t in tables)
            conn.execute("TRUNCATE {};".format(tnames))
            tx.commit()

    @classmethod
    def register(cls, context):
        context.db = DBContext()


def before_all(context):
    DBContext.register(context)

    TheApp.register(context, create_app(None, **TEST_SETTINGS))
    OAuth1Context.register(context)
    TheFixture.register(context)
    TheRequest.register(context)



def after_scenario(context, scenario):
    context.db.teardown()
    context.the_fixture.teardown()
