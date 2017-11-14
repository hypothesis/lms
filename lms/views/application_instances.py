from pyramid_mailer.message import Message
from pyramid.view import view_config
from lms.models import application_instance as ai


@view_config(route_name='welcome', request_method='POST', renderer='lms:templates/application_instances/create_application_instance.html.jinja2')
def create_application_instance(request):
    """Create application instance in the databse and respond with key and secret."""
    # TODO handle missing scheme in lms_url.

    instance = ai.build_from_lms_url(
        request.params['lms_url'],
        request.params['email']
    )
    request.db.add(instance)

    # TODO: Send email about signing up
    # TODO: tests
    # message = Message(
    #     subject="New key requested for Hypothesis LMS",
    #     sender="noreply@mysite.com",  # TODO: pull from configuration
    #     recipients=["keith.richards@atomicjolt.com"],  # TODO: pull from configuration
    #     body="""A new key for Hypothesis has been generated.
    #             URL: {0}
    #             Email: {1}
    #             """.format(request.params['lms_url'], request.params['email'])
    # )
    # mailer = request.mailer
    # mailer.send_immediately(message)

    return {
        'consumer_key': instance.consumer_key,
        'shared_secret': instance.shared_secret
    }


@view_config(
    route_name='welcome',
    renderer="lms:templates/application_instances/new_application_instance.html.jinja2"
)
def new_application_instance(_):
    """Render the form where users enter the lms url and email."""
    return {}
