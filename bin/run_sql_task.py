"""
Task runner for tasks written as SQL files in directories.

This is a general mechanism for running tasks defined in SQL, however it's
currently only used to perform the aggregations and mappings required for
reporting.
"""


from argparse import ArgumentParser

import importlib_resources
from psycopg2.extensions import parse_dsn
from pyramid.paster import bootstrap

from lms.models import Regions
from lms.sql_tasks.sql_script import SQLScript

TASK_ROOT = importlib_resources.files("lms.sql_tasks") / "tasks"

parser = ArgumentParser(
    description=f"A script for running SQL tasks defined in: {TASK_ROOT}"
)
parser.add_argument(
    "-c",
    "--config-file",
    required=True,
    help="The paster config for this application. (e.g. development.ini)",
)

parser.add_argument("-t", "--task", required=True, help="The SQL task name to run")


def main():
    args = parser.parse_args()

    with bootstrap(args.config_file) as env:
        request = env["request"]
        settings = env["registry"].settings

        Regions.set_region(settings["h_authority"])

        scripts = SQLScript.from_dir(
            task_dir=TASK_ROOT / args.task,
            template_vars={
                "db_user": parse_dsn(settings["database_url"].strip())["user"],
                "region": Regions.get_region(),
                # Hardcoded values to test GHA password masking
                "h_fdw_server_name": "h_fdw_server",
                "h_fdw_host": "h_postgres_1",
                "h_fdw_port": "5432",
                "h_fdw_dbname": "postgres",
                "h_fdw_user": "postgres",
                "h_fdw_password": "postgres",
                "h_fdw_tables": [
                    ("public", "annotation"),
                    ("public", "groups"),
                ],
            },
        )

        # Run the update in a transaction, so we roll back if it goes wrong
        with request.tm:
            with request.db.bind.connect() as connection:
                for script in scripts:
                    print(f"Executing: {script.path}")

                    for query in script.queries:
                        query.execute(connection)
                        print(query.dump(indent="    ") + "\n")


if __name__ == "__main__":
    main()
