from factory import Sequence, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

TaskDone = make_factory(
    models.TaskDone,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    key=Sequence(lambda n: f"task_done_key_{n}"),
)
