from lms.config.settings import env_setting
from pyramid.response import Response
from lms.models.users import User, find_by_lms_guid, build_from_lti_params

# TODO add tests
def associate_user(view_function):
    def wrapper(request, *args, **kwargs):
        lms_guid = request.params['user_id']
        result = find_by_lms_guid(request.db, lms_guid)

        if(result == None):
          new_user = build_from_lti_params(request.params)
          request.db.add(new_user)
          return view_function(request, *args, user=new_user, **kwargs)
        else:
          return view_function(request, *args, user=result, **kwargs)
    return wrapper
