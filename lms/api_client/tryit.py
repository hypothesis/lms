import os
from pprint import pprint

from lms.api_client.blackboard import BlackboardClient
from lms.api_client.generic_http.oauth2.manager import OAuth2Manager

access_token = "E3mxGJquiK2Z81zoMiY5u0yfNwlJwSMD"
access_token = "RUBBISH"
refresh_token = "153c176a9d704b6e86a352f36dbf2334:pkbcu6rTF6xBb2vWF82TbeCb2HuHejT5"

ws = BlackboardClient(host="blackboard.hypothes.is", access_token=access_token)
auth = OAuth2Manager(
    ws,
    client_id="e90b19eb-61c5-4a21-95ed-7afefcea273e",
    client_secret=os.environ["CLIENT_SECRET"],
    redirect_uri="https://httpbin.org/get",
    refresh_token=refresh_token,
)
api = ws.api()

#
# print('Auth URL:', auth.get_authorize_code_url())
# print(auth.get_tokens('6ezbWFC8ajSGKCndOjM7q8UHkt0yjDpL'))
# exit()

course_id = "uuid:07c0a521976e43b68616ad516adaab91"
course_id = "_16_1"

with auth.retry_session():
    # This won't retry
    pprint(api.version())

    # But this will as it's marked with @retriable
    # If it was called outside of the 'retry_session' it wouldn't retry
    pprint(api.course(course_id).list_contents())
