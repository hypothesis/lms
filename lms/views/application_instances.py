import logging

from pyramid.view import view_config
from pyramid_mailer.message import Message

from lms.models import application_instance as ai


@view_config(route_name='welcome', request_method='POST',
             renderer='lms:templates/application_instances/create_application_instance.html.jinja2')
def create_application_instance(request):
    """Create application instance in the databse and respond with key and secret."""
    # TODO handle missing scheme in lms_url.

    instance = ai.build_from_lms_url(
        request.params['lms_url'],
        request.params['email']
    )
    request.db.add(instance)

    _email_new_key_alert(
        settings=request.registry.settings,
        mailer=request.mailer,
        lms_url=request.params['lms_url'],
        email=request.params['email']
    )

    return {
        'consumer_key': instance.consumer_key,
        'shared_secret': instance.shared_secret
    }


def _email_new_key_alert(settings, mailer, lms_url, email):
    log = logging.getLogger(__name__)
    except_msg = ''
    email_body = "A new key for the Hypothesis LMS has been generated.\n" + \
                 f"URL: {lms_url}\nEmail:{email}"
    try:
        recipients = (settings['new_lms_email_recipient']).split(',')
        sender = settings['new_lms_email_sender']
        message = Message(
            subject="New key requested for Hypothesis LMS",
            sender=sender,
            recipients=recipients,
            body=email_body
        )

        mailer.send_immediately(message=message)
    except KeyError as e:
        except_msg = \
            "'new_lms_email_recipient' and 'new_lms_email_recipient' must " + \
            "be set in the ini file. Missing {}".format(e)
    except ConnectionRefusedError:
        except_msg = "No MTA accepted send email request. "
    finally:
        if except_msg:
            except_msg += "Email body:" + email_body.replace('\n', ' ')
            log.warning(except_msg)


@view_config(
    route_name='welcome',
    renderer="lms:templates/application_instances/new_application_instance.html.jinja2"
)
def new_application_instance(_):
    """Render the form where users enter the lms url and email."""
    return {}
