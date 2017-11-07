from pyramid.renderers import render_to_response

"""
  When using lti we dont have the benefit of being able to redirect because you can store a cookie
  in an iframe. As such, conditionally rendering views is necessary. This decorator provides
  a declarative way to render different views.
  You can decorate any function with this decorator the first argument to the decorator is the
  template you want to render. For example

  @view_renderer(renderer='lti:templates/lti_launches/new_lti_launch.html.jinja2')
  def some_view_function(request):
    return {
      ...
    }

  Just like if you specify a renderer with the view_config decorator, a function decorated with
  view_renderer simply needs to return a dict that contains the values that will be available in
  the template.

  Note that you can also pass any other values the the function, for example:

  @view_renderer(renderer='lti:templates/lti_launches/new_lti_launch.html.jinja2')
  def some_view_function(request, document_url):
    return {
      ...
    }

  The values are not positional arguments so their names must be used when invoking these
  functions.

  See views/lti_launches.py for some more example useage.
"""
def view_renderer(renderer):
  def view_decorator(view_function):
    def wrapper(request, **kwargs):
      return render_to_response(
        renderer,
        view_function(request, **kwargs),
        request=request
      )
    return wrapper
  return view_decorator
