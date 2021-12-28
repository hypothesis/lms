from pyramid.view import view_config
from celery.result import AsyncResult
from lms.tasks.celery import app


@view_config(
    request_method="POST",
    route_name="tasks_api.result",
    renderer="json",
)
def result(request):
    task = request.json["task"]

    res = AsyncResult(task["id"], app=app)

    return res.get()
