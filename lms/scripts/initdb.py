"""
A CLI command to initialize the database if it isn't already initialized.

Usage:

    initdb conf/development.ini
"""
import sys

from pyramid.paster import bootstrap


def initdb():
    # Initialise the pyramid environment, which is enough to trigger the
    # initialisation code in `lms.db.__init__.py` to setup the DB for us.
    bootstrap(sys.argv[1])
