import inspect

__all__ = ["instantiate_schema"]


def instantiate_schema(schema, request):
    # Schemas can just be dicts or they can be actual
    # marshmallow.Schema subclasses, in which case we need to
    # instantiate the class.
    if inspect.isclass(schema):
        schema = schema()
        schema.context["request"] = request

    return schema
