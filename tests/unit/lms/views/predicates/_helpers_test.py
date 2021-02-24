import pytest

from lms.views.predicates._helpers import Base


class TestBase:
    # pylint:disable=abstract-method,abstract-class-instantiated

    def test_subclasses_must_have_name(self):
        class CustomPredicateFactory(Base):
            def __call__(self, context, request):
                """Do nothing."""

        with pytest.raises(
            TypeError,
            match="Can't instantiate abstract class CustomPredicateFactory with abstract methods? name",
        ):
            CustomPredicateFactory("test_value", "test_config")

    def test_subclasses_must_have___call__(self):
        class CustomPredicateFactory(Base):
            name = "custom_predicate_factory"

        with pytest.raises(
            TypeError,
            match="Can't instantiate abstract class CustomPredicateFactory with abstract methods? __call__",
        ):
            CustomPredicateFactory("test_value", "test_config")

    def test_value(self):
        # It makes self.value available to subclasses.
        assert (
            CustomPredicateFactory("test_value", "test_config").get_value()
            == "test_value"
        )

    def test_config(self):
        # It makes self.config available to subclasses.
        assert (
            CustomPredicateFactory("test_value", "test_config").get_config()
            == "test_config"
        )

    def test_text(self):
        assert (
            CustomPredicateFactory("test_value", "test_config").text()
            == "custom_predicate_factory = test_value"
        )

    def test_phash(self):
        assert (
            CustomPredicateFactory("test_value", "test_config").phash()
            == "custom_predicate_factory = test_value"
        )


class CustomPredicateFactory(Base):
    name = "custom_predicate_factory"

    def __call__(self, context, request):
        """Do nothing."""

    def get_value(self):
        return self.value

    def get_config(self):
        return self.config
