from collections import defaultdict
from datetime import datetime
from typing import Iterator, List

from lms.services.digest._digest_assistant import DigestAssistant
from lms.services.digest._models import Digest
from lms.services.h_api import HAPI
from lms.services.mailchimp import EmailSender, MailchimpService


class DigestService:
    """A service for getting digests and emailing them to people."""

    def __init__(
        self,
        digest_assistant: DigestAssistant,
        h_api: HAPI,
        mailchimp_service: MailchimpService,
        sender: EmailSender,
    ):
        self._assistant = digest_assistant
        self._h_api = h_api
        self._mailchimp_service = mailchimp_service
        self._sender = sender

    def send_emails(
        self,
        audience: List[str],
        updated_after: datetime,
        updated_before: datetime,
        override_to_email: str = None,
    ):
        """
        Prepare and send activity digests for users over the given period.

        :param audience: List of H userids to send digests to
        :param updated_after: Search for activity after this date
        :param updated_before: Search for activity before this date
        :param override_to_email: Optional override to the destination email
            address for testing purposes
        """
        for digest in self.get_digests(audience, updated_after, updated_before):
            template_vars = digest.serialize()

            if override_to_email:
                digest.audience_user.email = override_to_email

            # Check we have something worth sending, and someone to send it to
            if template_vars["total_annotations"] and digest.audience_user.email:
                self._mailchimp_service.send_template(
                    template_name="instructor-email-digest",
                    sender=self._sender,
                    recipient=digest.audience_user,
                    template_vars=template_vars,
                )

    def get_digests(
        self, audience: List[str], updated_after: datetime, updated_before: datetime
    ) -> Iterator[Digest]:
        """
        Get activity digests for users over a period.

        :param audience: List of H userids to send digests to
        :param updated_after: Search for activity after this date
        :param updated_before: Search for activity before this date
        """
        annotations = self._h_api.get_annotations(
            audience, updated_after, updated_before
        )
        if not annotations:
            return

        courses = self._assistant.get_h_courses(
            authority_provided_ids={
                annotation["group"]["authority_provided_id"]
                for annotation in annotations
            }
        )
        self._add_annotations_to_courses(courses, annotations)
        instructors_to_courses = self._map_instructors_to_courses(courses)

        for audience_user in self._assistant.get_h_users(h_userids=audience):
            yield Digest(
                audience_user=audience_user,
                courses=instructors_to_courses.get(audience_user.h_userid, []),
            )

    @classmethod
    def _map_instructors_to_courses(cls, courses):
        # Make a mapping from h-userid to course
        instructors_to_courses = defaultdict(list)
        for course in courses:
            for h_userid in course.instructors:
                instructors_to_courses[h_userid].append(course)

        return instructors_to_courses

    @classmethod
    def _add_annotations_to_courses(cls, courses, annotations):
        # Make a mapping from authority_provided_id to annotation
        authority_id_to_annotation = defaultdict(list)
        for annotation in annotations:
            authority_id = annotation["group"]["authority_provided_id"]
            authority_id_to_annotation[authority_id].append(annotation)

        # Map annotations to courses
        for course in courses:
            annotations = []
            for authority_id in course.aka:
                annotations.extend(authority_id_to_annotation.get(authority_id, []))

            course.annotations = annotations
