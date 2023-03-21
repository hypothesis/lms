from lms.services.digest._digest_assistant import DigestAssistant
from lms.services.digest.service import DigestService
from lms.services.h_api import HAPI
from lms.services.mailchimp import EmailSender, MailchimpService


def service_factory(_context, request) -> DigestService:
    """Get a digest service object."""

    return DigestService(
        digest_assistant=DigestAssistant(request.db),
        h_api=request.find_service(HAPI),
        mailchimp_service=request.find_service(MailchimpService),
        sender=EmailSender(
            subaccount=request.registry.settings.get("mailchimp_digests_subaccount"),
            email=request.registry.settings.get("mailchimp_digests_email"),
            name=request.registry.settings.get("mailchimp_digests_name"),
        ),
    )
