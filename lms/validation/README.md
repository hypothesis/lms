# Validation Schemas

Guard schemas for views.

## What's in this package?

This packages contains:

1. Validation schemas for guarding views
2. Exceptions raised by guard schemas
2. Base classes and other helpers for implementing validation schemas

### 1. Guard schemas for views

This package contains validation schemas that are used to guard views: they
parse and validate Pyramid requests before the view is called, and ensure that
the view won't even be called if the request isn't valid.
See [`__init__.py`](__init__.py)'s docstring for usage.

### 2. Exceptions raised by guard schemas

[lms.validation.exceptions](exceptions.py) contains exceptions classes that
guard schemas might raise if the request is invalid.
These exceptions are caught by exception views that render the appropriate
error responses.

### 3. Base classes and other helpers for validation schemas

[lms.validation.base](base.py) contains base classes for validation schemas.
You are encouraged to use these base classes where you need to, even when
implementing schemas outside of this package.

In future this package might also export other kinds of helpers for
implementing schemas, if they might be useful outside of this package.

## What shouldn't be in this package?

Not all validation schemas are used for guarding views. For example:

* It's often useful to write a schema just to parse some params out
  of a request or even just out of a dict. Rather than being used to guard a
  view, these schemas would be imported and called by some other part of the
  code (for example, maybe a service) that wants to get at some params:

  ```python
  try:
      foo_params = FooSchema(request).parse()
  except marshmallow.ValidationError:
      # It was not possible to parse the "foo params" out of this request.
      ...
  ```

  Schemas like this should live near the code that uses them for better
  localization. They shouldn't live in this package, far away from the code
  that calls them, just because they're validation schemas. This package is
  specifically for view guards, which are a particular type of schema used in
  `@view_config`'s and called at a particular stage in the request processing
  pipeline.

* It's often useful to write a schema to parse a `requests`-library _response_,
  rather than to parse a Pyramid request.

  Again, these schemas would not be used to guard views but would be imported
  and called by some code that needs to parse some params out of a response:

  ```python
  response = requests.get(...)

  try:
      parsed_params = BarSchema(response).parse()
  except marshmallow.ValidationError as err:
      # The response was invalid.
      ...
  ```

Although they don't live in this package, external schemas can still import and
use base classes and other helpers from this package's public interface.
