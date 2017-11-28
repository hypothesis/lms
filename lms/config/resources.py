from pyramid.security import Allow, Everyone


class Root(object):
    __acl__ = [(Allow, 'group:report_viewers', 'view')]

    def __init__(self, request):
        pass