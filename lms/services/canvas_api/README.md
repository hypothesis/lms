# Canvas API Client

## The class layout

There are a number of different API clients which deal with the API at varying
different levels. They all sit inside the `public_client.CanvasAPIClient` in
a nested fashion:

 * [`public.CanvasAPIClient`](public.py) - High level API access
 * [`authenticated.AuthenticatedClient`](authenticated.py) - OAuth2 token handling
 * [`basic.BasicClient`](basic.py) - HTTP marshalling, requests and applying schema

To see how these are all bolted together see: [`__init__.py`](__init__.py)

## Getting authenticated users sections

[Canvas's sections API](https://canvas.instructure.com/doc/api/sections.html) only allows
you to get _all_ of a course's sections, it doesn't provide a way to
get only the sections that the authenticated user belongs to. So we
have to get the authenticated user's sections from part of the
response from a courses API endpoint instead.

Canvas's "Get a single course" API is capable of doing this if the
`?include[]=sections` query param is given:

* https://canvas.instructure.com/doc/api/courses.html#method.courses.show

The `?include[]=sections` query param is documented elsewhere (in the
"List your courses" API:

 * https://canvas.instructure.com/doc/api/courses.html#method.courses.index)
as:


>  Section enrollment information to include with each Course.
   Returns an array of hashes containing the section ID (id), section
   name (name), start and end dates (start_at, end_at), as well as the
   enrollment type (enrollment_role, e.g. 'StudentEnrollment').

In practice `?include[]=sections` seems to add a "sections" key to the
API response that is a list of section dicts, one for each section
the authenticated user is currently enrolled in, each with the
section's "id" and "name" among other fields.

**We don't know what happens if the user belongs to a really large
number of sections**. Does the list of sections embedded within the
get course API response just get really long? Does it get truncated?
Can you paginate through it somehow? This seems edge-casey enough
that we're ignoring it for now.