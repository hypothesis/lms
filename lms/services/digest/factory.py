from lms.services.digest.service import DigestService
from lms.services.h_api import HAPI
from lms.services.mailchimp import EmailSender, MailchimpService


def service_factory(_context, request):
    return DigestService(
        db=request.db,
        h_api=request.find_service(HAPI),
        mailchimp_service=request.find_service(MailchimpService),
        sender=EmailSender(
            request.registry.settings.get("mailchimp_digests_subaccount"),
            request.registry.settings.get("mailchimp_digests_email"),
            request.registry.settings.get("mailchimp_digests_name"),
        ),
    )
