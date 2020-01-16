import os
from contextlib import contextmanager
from datetime import datetime
from pprint import pprint

from requests import Session

from lms.api_client.blackboard_classic import BlackboardClassicClient
from lms.api_client.blackboard_classic.model import File, Folder
from lms.api_client.generic_http.oauth2.manager import OAuth2Manager


@contextmanager
def timeit():
    start = datetime.utcnow()
    yield

    diff = datetime.utcnow() - start
    print(diff.microseconds / 1000 + diff.seconds * 1000, "ms")


access_token = "EKkvbCBN26W8hICpZiG4XtZ1vQr8uOMh"
refresh_token = "153c176a9d704b6e86a352f36dbf2334:sRhnwClYrgqP6pWUzT594sXQZGflIbs0"


def token_callback(token_response):
    print("NEW TOKENS!")
    pprint(token_response)


ws = BlackboardClassicClient(host="blackboard.hypothes.is")
auth = OAuth2Manager(
    ws,
    client_id="e90b19eb-61c5-4a21-95ed-7afefcea273e",
    client_secret=os.environ["CLIENT_SECRET"],
    redirect_uri="https://httpbin.org/get",
    token_callback=token_callback,
).set_tokens(access_token=access_token, refresh_token=refresh_token,)

api = ws.api()
course_id = "07c0a521976e43b68616ad516adaab91"


with auth.session():
    print("Auth URL:", auth.get_authorize_code_url())
    print(auth.get_tokens("4R6bW6JeSGv8lqyROSODugaNlfsNhES7"))

    # This won't _retry_handler
    pprint(api.version())

    course = api.course(course_id)

    # But this will as it's marked with @retriable
    # If it was called outside of the 'session' it wouldn't _retry_handler
    stack = list(course.list_contents())

    while stack:
        item = stack.pop()

        if isinstance(item, Folder) and item.has_children:
            print(f"{item.title}/ #{item.id}")
            stack.extend(item.children())

        elif isinstance(item, File):
            # if item.extension != 'pdf':
            #    continue

            print(f"{item.filename} #{item.id}")
            print("Retrieval id", item.retrieval_id)

            c_id, ct_id = item.retrieval_id.split("/")
            with timeit():
                attachment = api.course(c_id).content(ct_id).first_attachment()

            # with timeit():
            #     print(attachment.download_url)

            print(attachment.api.template())
            print(attachment.api.ws.get_url(attachment.api.path()))

            print("ATT_ID", attachment.id)
