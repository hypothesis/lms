"""
Task runner for tasks written as SQL files in directories.

This is a general mechanism for running tasks defined in SQL, however it's
currently only used to perform the aggregations and mappings required for
reporting.
"""  # noqa: EXE002

from argparse import ArgumentParser

import data_tasks
import importlib_resources
from data_tasks.python_script import PythonScript
from psycopg2.extensions import parse_dsn
from pyramid.paster import bootstrap

TASK_ROOT = importlib_resources.files("lms.data_tasks")

parser = ArgumentParser(
    description=f"A script for running tasks defined in: {TASK_ROOT}"
)
parser.add_argument(
    "-c",
    "--config-file",
    required=True,
    help="The paster config for this application. (e.g. development.ini)",
)

parser.add_argument("-t", "--task", required=True, help="The data task name to run")

parser.add_argument(
    "--no-python",
    action="store_const",
    default=False,
    const=True,
    help="Skip Python executables",
)
parser.add_argument(
    "--dry-run",
    action="store_const",
    default=False,
    const=True,
    help="Run through the task without executing anything for real",
)


def main():
    args = parser.parse_args()

    with bootstrap(args.config_file) as env:
        request = env["request"]
        settings = env["registry"].settings

        scripts = data_tasks.from_dir(
            task_dir=TASK_ROOT / args.task,
            template_vars={
                "db_user": parse_dsn(settings["database_url"].strip())["user"],
                "h_authority": settings["h_authority"],
                "h_fdw": parse_dsn(settings["h_fdw_database_url"]),
                "fdw_users": settings["fdw_users"],
            },
        )

        # Run the update in a transaction, so we roll back if it goes wrong
        with request.db.bind.connect() as connection:  # noqa: SIM117
            with connection.begin():
                for script in scripts:
                    if args.no_python and isinstance(script, PythonScript):
                        print(f"Skipping: {script}")  # noqa: T201
                        continue

                    for step in script.execute(connection, dry_run=args.dry_run):
                        if args.dry_run:
                            print("Dry run!")  # noqa: T201

                        print(step.dump(indent="    ") + "\n")  # noqa: T201


if __name__ == "__main__":
    main()
