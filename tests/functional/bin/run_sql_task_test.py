import os
import sys
from subprocess import check_output

import pytest
from importlib_resources import files
from pytest import fixture

from tests.functional.conftest import TEST_ENVIRONMENT


class TestRunSQLTask:
    def test_sanity(self, environ):
        self.run_task(environ, "hello_world")

    # We use "db_engine" here to ensure the schema is created
    @pytest.mark.usefixtures("db_engine")
    # If you want to run these tests, you first need to start services in H
    # and run the `report/create_from_scratch` task there.
    @pytest.mark.xfail(reason="Requires reporting tasks to be run in H")
    def test_reporting_tasks(self, environ):
        for task_name in (
            "report/create_from_scratch",
            "report/refresh",
            "report/create_from_scratch",
        ):
            self.run_task(environ, task_name)

    def run_task(self, environ, task_name):
        result = check_output(
            [
                sys.executable,
                "bin/run_sql_task.py",
                "--config-file",
                "conf/development.ini",
                "--task",
                task_name,
            ],
            env=environ,
        )

        assert result

        print(f"Task {task_name} OK!")
        print(result.decode("utf-8"))

    @fixture
    def environ(self):
        environ = dict(os.environ)

        environ["PYTHONPATH"] = "."
        environ.update(TEST_ENVIRONMENT)

        return environ

    @fixture(autouse=True)
    def run_in_root(self):
        # A context manager to ensure we work from the root, but return the
        # path to where it was before
        current_dir = os.getcwd()
        os.chdir(str(files("lms") / ".."))

        yield

        os.chdir(current_dir)
