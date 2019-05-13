"""Helpers for handling marshmallow schemas."""
import inspect


__all__ = ["instantiate_schema"]


def instantiate_schema(schema, request):
    """
    Return an instance of ``schema`` with ``request`` as context.

    Webargs schemas can just be dicts, in which case they don't need to be
    instantiated and can just be used directly to parse a request.

    Or they can be actual :class:`marshmallow.Schema` subclasses, in which case
    they need to be instantiated and the instance, not the class, is used to
    parse the request.

    Return ``schema`` unmodified if it's a dict or, if ``schema`` is a class,
    then instantiate it, add ``request`` to the instance's context, and return
    the instance. Either way the returned schema object can now be used to
    parse a request.
    """
    if inspect.isclass(schema):
        schema = schema()
        schema.context["request"] = request

    return schema
