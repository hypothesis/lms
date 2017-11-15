import logging

from pyramid.view import view_config
from pyramid_mailer.message import Message

from lms.models import application_instance as ai


@view_config(route_name='welcome', request_method='POST',
             renderer='lms:templates/application_instances/create_application_instance.html.jinja2')
def create_application_instance(request):
    """Create application instance in the databse and respond with key and secret."""
    # TODO handle missing scheme in lms_url.

    log = logging.getLogger(__name__)

    instance = ai.build_from_lms_url(
        request.params['lms_url'],
        request.params['email']
    )
    request.db.add(instance)

    # TODO: tests
    settings = request.registry.settings
    except_msg = ''
    email_body = "A new key for the Hypothesis LMS has been generated.\n" + \
                 f"URL: {request.params['lms_url']}\nEmail:{request.params['email']}"
    try:
        recipients = (settings['new_lms_email_recipient']).split(',')
        sender = settings['new_lms_email_sender']

        message = Message(
            subject="New key requested for Hypothesis LMS",
            sender=sender,
            recipients=recipients,
            body=email_body
        )
        mailer = request.mailer
        mailer.send_immediately(message)
    except KeyError as e:
        except_msg = "'new_lms_email_recipient' and 'new_lms_email_recipient' must be set in the ini file. Missing {}".format(
            e)
    except ConnectionRefusedError:
        except_msg = "No MTX accepted send email request. "
    finally:
        if except_msg:
            except_msg += "Email body:" + email_body.replace('\n', ' ')
            log.warning(except_msg)

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
