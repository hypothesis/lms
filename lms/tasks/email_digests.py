from datetime import datetime, timedelta, timezone

import mailchimp_transactional
from sqlalchemy import text
from mailchimp_transactional.api_client import ApiClientError

from lms.models import Grouping, GroupingMembership, LTIRole, User, UserSettings
from lms.services import EmailDigestsService
from lms.tasks.celery import app


@app.task
def schedule_email_digests():
    with app.request_context() as request:  # pylint:disable=no-member
        request.tm.begin()

        users = (
            request.db.query(User)
            .join(UserSettings, User.h_userid == UserSettings.h_userid)
            .filter(UserSettings.instructor_email_digests.is_(True))
        )

        # This task is meant to be run shortly after 5AM UTC each morning.
        # The email digests that will be sent will cover annotation activity
        # over a 24hr period from 5AM UTC yesterday morning until 5AM UTC this
        # morning.
        # 5AM UTC has been chosen because it equates to midnight EST. Most of
        # our target users for this feature are in the EST timezone and we want
        # each email digest to be sent shortly after midnight EST and to cover
        # "yesterday" (midnight to midnight) EST.
        # EST is 5 hours behind UTC (ignoring daylight savings for simplicity).
        now = datetime.now(timezone.utc)
        previous_midnight = datetime(year=now.year, month=now.month, day=now.day)
        since = previous_midnight - timedelta(days=1) + timedelta(hours=5)
        until = previous_midnight + timedelta(hours=5)

        for user in users:
            send_email_digest.apply_async((user.id, since, until))


@app.task
def send_email_digest(user_id, since, until):
    since = datetime.fromisoformat(since)
    until = datetime.fromisoformat(until)

    with app.request_context() as request:  # pylint:disable=no-member
        request.tm.begin()
        svc = request.find_service(EmailDigestsService)

        activity = svc.get(user_id, since=since, until=until)

        # The params that we'll post to Mailchimp Transactional's send-template API:
        # https://mailchimp.com/developer/transactional/api/messages/send-using-message-template/
        params = {
            "template_name": "instructor_email_digest",
            "template_content": [{}],
            "message": {
                "subaccount": "<INSERT_SUBACCOUNT_ID>",
                "from_email": "<INSERT_FROM_ADDRESS>",
                "from_name": "Hypothesis",
                "to": [{"email": "<INSERT_TO_ADDRESS>", "name": "Sean Hammond"}],
                "track_opens": True,
                "track_clicks": True,
                "global_merge_vars": [
                    {"name": "num_annotations", "content": activity["num_annotations"]},
                    {"name": "courses", "content": activity["courses"]},
                ],
            },
            "async": True,
        }

        mailchimp_api_key = request.registry.settings["mailchimp_api_key"]

        if mailchimp_api_key:
            mailchimp_client = mailchimp_transactional.Client(mailchimp_api_key)
            print("Actually calling Mailchimp...")
            print(params)
            mailchimp_client.messages.send_template(params)
        else:
            print("No Mailchimp API key")
            print(params)
