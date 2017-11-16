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
        pyramid_request.mailer = pyramid_mailer.mailer.DummyMailer

        create_application_instance(pyramid_request)

        assert pyramid_request.db.query(ApplicationInstance).filter(
            ApplicationInstance.lms_url == pyramid_request.params[
                'lms_url']).count() == 1

    def test_log_when_no_email_settings(self, pyramid_request, capfd):
        pyramid_request.method = 'POST'
        pyramid_request.params = {
            'lms_url': 'canvas.example.com',
            'email': 'email@example.com',
        }
        pyramid_request.mailer = pyramid_mailer.mailer.DummyMailer
        
        create_application_instance(pyramid_request)

        out, err = capfd.readouterr()
        assert 'new_lms_email_recipient' in err
        assert 'new_lms_email_recipient' in err

    # def test_log_when_no_mta(self, pyramid_request, pyramid_config, capfd):
    #     pyramid_config.registry.settings[
    #         'new_lms_email_recipient'] = 'recipient@hypothes.is'
    #     pyramid_config.registry.settings[
    #         'new_lms_email_sender'] = 'sender@hypothes.is'
    #     pyramid_request.method = 'POST'
    #     pyramid_request.params = {
    #         'lms_url': 'canvas.example.com',
    #         'email': 'email@example.com',
    #     }
    #
    #     pyramid_request.mailer = pyramid_mailer.mailer.DummyMailer
    #
    #     create_application_instance(pyramid_request)
    #
    #     out, err = capfd.readouterr()
    #     assert 'new_lms_email_recipient' in err
    #     assert 'new_lms_email_recipient' in err
