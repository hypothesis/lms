import socket
import pyramid_mailer

from lms.views import create_application_instance
from lms.models import ApplicationInstance


class TestApplicationInstance(object):
    def test_it_creates_an_application_instance(self, pyramid_request):
        pyramid_request.method = 'POST'
        pyramid_request.params = {
            'lms_url': 'canvas.example.com',
            'email': 'email@example.com',
        }
        initial_count = pyramid_request.db.query(ApplicationInstance).filter(
            ApplicationInstance.lms_url == pyramid_request.params['lms_url']).count()
        pyramid_request.mailer = pyramid_mailer.mailer.DummyMailer()

        create_application_instance(pyramid_request)
        new_count = pyramid_request.db.query(ApplicationInstance).filter(
            ApplicationInstance.lms_url == pyramid_request.params['lms_url']).count()
        assert new_count == initial_count + 1

    def test_log_when_no_email_settings(self, pyramid_request, capfd):
        pyramid_request.method = 'POST'
        pyramid_request.params = {
            'lms_url': 'canvas.example.com',
            'email': 'email@example.com',
        }
        pyramid_request.mailer = pyramid_mailer.mailer.DummyMailer()

        create_application_instance(pyramid_request)

        _, err = capfd.readouterr()
        assert 'new_lms_email_recipient' in err
        assert 'new_lms_email_recipient' in err

    def test_send_email_when_new_key_created(
            self, pyramid_request,
            pyramid_config
    ):
        pyramid_config.registry.settings[
            'new_lms_email_recipient'] = 'recipient@hypothes.is'
        pyramid_config.registry.settings[
            'new_lms_email_sender'] = 'sender@hypothes.is'
        pyramid_request.method = 'POST'
        pyramid_request.params = {
            'lms_url': 'canvas.example.com',
            'email': 'email@example.com',
        }

        pyramid_request.mailer = pyramid_mailer.mailer.DummyMailer()

        create_application_instance(pyramid_request)

        is_msg_sent = False
        for message in pyramid_request.mailer.outbox:
            if 'A new key for the Hypothesis LMS has been generated' in message.body:
                is_msg_sent = True

        assert is_msg_sent

    def test_log_when_no_mta_accepts_email(self, pyramid_request,
                                           pyramid_config, capfd):
        pyramid_config.registry.settings[
            'new_lms_email_recipient'] = 'recipient@hypothes.is'
        pyramid_config.registry.settings[
            'new_lms_email_sender'] = 'sender@hypothes.is'
        pyramid_request.method = 'POST'
        pyramid_request.params = {
            'lms_url': 'canvas.example.com',
            'email': 'email@example.com',
        }
        pyramid_request.mailer = pyramid_mailer.mailer.Mailer()

        # If the email port is not used, we can test a failed attempt to send
        #  an email. If it is used, abort the test. We don't want to actually
        #  send an email.
        mta_socket = socket.socket()
        try:
            connection_results = mta_socket.connect_ex(('localhost', 25))
            assert connection_results != 0

            create_application_instance(pyramid_request)

            _, err = capfd.readouterr()
            assert 'No MTA accepted send email request.' in err
        except OSError:
            print("github's Travis throws this error. Just give up on the test")
