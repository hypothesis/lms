"""Decorator to find a user from the lms user_id guid."""
from lms.models.users import find_by_lms_guid, build_from_lti_params


def associate_user(view_function):
    """
    Decorate a view function to find a user from the lms user_id guid.

    This is expected to be used during an lti launch. If no user is found
    associated with the user_id then a new user will be created.
    """
    def wrapper(request, *args, **kwargs):
        """Look for a user with a matching lms_guid."""
        lms_guid = request.params['user_id']
        result = find_by_lms_guid(request.db, lms_guid)
        if result is None:
            new_user = build_from_lti_params(request.params)
            request.db.add(new_user)
            return view_function(request, *args, user=new_user, **kwargs)
        return view_function(request, *args, user=result, **kwargs)
    return wrapper
