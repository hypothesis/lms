# Validators

## What is in this directory?

### Guard schemas for views

This directory contains schemas that are used as guards on view classes.

They define a set of parameters which are required to call a particular view
and are added as a `schema` as part of a view directory like this:

```python
@view_defaults(schema=LaunchParamsSchema)
```

### Base classes for validators

 * [lms.validators.base](base.py) - Defines base classes for validators
 * [lms.validators.exceptions](exceptions.py) - Defines exceptions which
   can be raised during validation intended to be caught by error views

You are encouraged to use these classes where it you need to, even outside
of this directory.

## What shouldn't be in this directory?

 * There are lots of schema which are just used to pick things out of dicts
 * They should live with the code that uses them
 * This makes it easier to read that code
