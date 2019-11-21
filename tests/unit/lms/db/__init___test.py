import sqlalchemy as sa

from lms.db import BASE


class Child(BASE):
    __tablename__ = "child"
    id = sa.Column(sa.Integer, primary_key=True)


class ModelClass(BASE):
    __tablename__ = "model_class"
    id = sa.Column(sa.Integer, primary_key=True)
    column = sa.Column(sa.Integer, sa.ForeignKey("child.id"))
    relationship = sa.orm.relationship("Child")


class TestBase:
    def test_we_can_get_properties(self):
        keys = {prop.key for prop in ModelClass.iter_properties()}

        assert {"id", "relationship", "column"} == keys

    def test_we_can_get_columns(self):
        keys = {prop.key for prop in ModelClass.iter_columns()}

        assert {"id", "column"} == keys
