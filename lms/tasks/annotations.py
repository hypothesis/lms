import logging

from sqlalchemy import select

from lms.models import Assignment, LMSUser
from lms.services.mailchimp import EmailRecipient, EmailSender
from lms.tasks.celery import app

LOG = logging.getLogger(__name__)


@app.task
def process_annotation(*, event) -> None:
    if event["action"] != "create":
        return

    with app.request_context() as request, request.tm:
        mentioning_user = request.db.scalar(
            select(LMSUser).where(LMSUser.h_userid == event["annotation"]["user"])
        )

        assignment = request.db.scalar(
            select(Assignment).where(
                Assignment.tool_consumer_instance_guid
                == event["annotation"]["metadata"]["lms"]["guid"],
                Assignment.resource_link_id
                == event["annotation"]["metadata"]["lms"]["assignment"][
                    "resource_link_id"
                ],
            )
        )

        # TODO assert the assignment matches the annotations group (ie, the assignment belongs to the course of the group)
        course = assignment.course

        # TODO ignore non-`shared`
        for mention in event["annotation"]["mentions"]:
            mentioned_user = request.db.scalar(
                select(LMSUser).where(LMSUser.h_userid == mention["userid"])
            )

            if not mentioned_user.email:
                # If mentioned user doesn't have an email address we can't email them.
                continue

            if mentioned_user == mentioning_user:
                # If the mentioning user mentions self, we don't want to send an email.
                continue

            if not event["annotation"]["document"]:
                # If the annotation doesn't have a document, we can't send an email.
                continue

            print(
                f"{mentioned_user.display_name} was mentioned by {mentioning_user.display_name} in course {course.lms_name} assignment {assignment.title}"
            )

            # TODO, task done
            task_done_key = None
            task_done_data = None

            sender = EmailSender(
                request.registry.settings.get("mailchimp_digests_subaccount"),
                request.registry.settings.get("mailchimp_digests_email"),
                request.registry.settings.get("mailchimp_digests_name"),
            )

            template_vars = {
                "preferences_url": self._email_preferences_service.preferences_url(
                    mentioned_user.h_userid, "instructor_digest"
                ),
                "mentioning_user": mentioning_user.display_name,
            }

            send.delay(
                task_done_key=task_done_key,
                task_done_data=task_done_data,
                template="lms:templates/email/annotation_mention/",
                sender=asdict(sender),
                recipient=asdict(
                    EmailRecipient(mentioned_user.email, mentioned_user.display_name)
                ),
                template_vars=template_vars,
                unsubscribe_url=self._email_preferences_service.unsubscribe_url(
                    context.user_info.h_userid, "instructor_digest"
                ),
            )
