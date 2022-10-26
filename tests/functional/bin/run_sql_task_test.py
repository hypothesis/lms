import os
import sys
from subprocess import check_output

import pytest
from importlib_resources import files
from pytest import fixture

from tests.functional.conftest import TEST_ENVIRONMENT


class TestRunSQLTask:
    # We use "db_engine" here to ensure the schema is created
    @pytest.mark.usefixtures("db_engine")
    def test_reporting_tasks(self, environ):
        for task_name in ("hello_world",):
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
