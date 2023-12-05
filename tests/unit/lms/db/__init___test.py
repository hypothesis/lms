import sqlalchemy as sa

from lms.db import BASE


class Child(BASE):
    __tablename__ = "child"
    id = sa.Column(sa.Integer, primary_key=True)


class ModelClass(BASE):
    __tablename__ = "model_class"
    _aliased_column = sa.Column("aliased_column", sa.Integer)
    id = sa.Column(sa.Integer, primary_key=True)
    column = sa.Column(sa.Integer, sa.ForeignKey("child.id"))
    relationship = sa.orm.relationship("Child")


class TestBase:
    def test_we_can_get_columns(self):
        assert sorted(ModelClass.columns()) == [
            "_aliased_column",
            "column",
            "id",
        ]

    def test_repr(self):
        model = ModelClass(_aliased_column=77, id=23, column=46)

        assert repr(model) == "ModelClass(_aliased_column=77, id=23, column=46)"

    def test_repr_is_valid_python(self):
        model = ModelClass(id=23, column=46)

        deserialized_model = eval(repr(model))  # pylint:disable=eval-used

        for attr in (
            "id",
            "column",
        ):
            assert getattr(deserialized_model, attr) == getattr(model, attr)
