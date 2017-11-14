from pyramid_mailer.message import Message
from pyramid.view import view_config
from pyramid.paster import get_appsettings
from lms.models import application_instance as ai
import logging


@view_config(route_name='welcome', request_method='POST', renderer='lms:templates/application_instances/create_application_instance.html.jinja2')
def create_application_instance(request):
    """Create application instance in the databse and respond with key and secret."""
    # TODO handle missing scheme in lms_url.

    instance = ai.build_from_lms_url(
        request.params['lms_url'],
        request.params['email']
    )
    request.db.add(instance)

    # TODO: tests
    # import pdb; pdb.set_trace()
    settings = get_appsettings('conf/development.ini', name='main')
    recipient = settings['new_lms_email_recipient']
    message = Message(
        subject="New key requested for Hypothesis LMS",
        sender=settings['new_lms_email_sender'],
        recipients=[recipient, ],
        body="A new key for the Hypothesis LMS has been generated.\nURL: {0}\nEmail:{1}".format(request.params['lms_url'], request.params['email'])
    )
    mailer = request.mailer
    try:
        mailer.send_immediately(message)
    except ConnectionRefusedError:
        msg = "No MTX accepted send email request. Email body:\n"
        msg += message.body
        log = logging.getLogger(__name__)
        log.warning(msg)

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
