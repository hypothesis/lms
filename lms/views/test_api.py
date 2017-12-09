from pyramid.view import view_config
from lms.util.canvas_api import CanvasApi, GET
from lms.config.settings import env_setting


@view_config(route_name='test_api', renderer='string', request_method='GET')
def test_api(request):
    canvas_api = CanvasApi(
      env_setting('CANVAS_TOKEN'),
      'https://atomicjolt.instructure.com'
    )
    response = canvas_api.get_canvas_course_files(253, {})
    data = response.json()
    return data