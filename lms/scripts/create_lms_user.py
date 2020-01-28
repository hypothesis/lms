import sys

from pyramid.paster import bootstrap


__all__ = ["create_lms_user"]


def create_lms_user():
    with bootstrap(sys.argv[1]) as env:
        env["request"].find_service(name="h_api").create_lms_user()
