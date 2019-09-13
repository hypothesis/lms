__all__ = ("is_instructor",)


def is_instructor(request):
    """
    Indicate whether the current request represents an LTI instructor (teacher).

    TODO: This application should have a real authorization layer.
    """
    return any(
        role in request.lti_user.roles.lower()
        for role in ("administrator", "instructor", "teachingassistant")
    )
