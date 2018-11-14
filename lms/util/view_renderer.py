"""Provide functionality for conditionally rendering views in a declarative way."""
from pyramid.renderers import render_to_response


def view_renderer(renderer):
    def view_decorator(view_function):
        def wrapper(request, **kwargs):
            """Return a response object that pyramid can use."""
            return render_to_response(
                renderer, view_function(request, **kwargs), request=request
            )

        return wrapper

    return view_decorator
