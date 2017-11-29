from pyramid.security import Allow, Everyone


class Root(object):
    __acl__ = [(Allow, 'report_viewer', 'view')]

    def __init__(self, request):
        pass