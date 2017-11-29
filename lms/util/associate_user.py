from lms.config.settings import env_setting
from pyramid.response import Response


def associate_user(view_function):
    def wrapper(request):
        import pdb; pdb.set_trace()
        return view_function(request)
    return wrapper
