import oauthlib
from oauthlib.oauth1 import SIGNATURE_HMAC_SHA1, SIGNATURE_TYPE_BODY


class VitalSourceService:
    def __init__(self, _context, request):
        self._oauth_key = request.registry.settings["vitalsource_launch_key"]
        self._oauth_secret = request.registry.settings["vitalsource_launch_secret"]

    def get_launch_params(self, book_id, cfi, lti_user):
        """
        Launch the VitalSource book viewer using an LTI launch.

        See https://developer.vitalsource.com/hc/en-us/articles/215612237-POST-LTI-Create-a-Bookshelf-Launch
        """

        launch_url = f"https://bc.vitalsource.com/books/{book_id}"

        if cfi:
            book_location = "/cfi" + cfi

        launch_params = self._launch_params(
            # TODO - Set the real user ID and roles here.
            user_id="teststudent",
            roles="Learner",
            # user_id=lti_user.user_id,
            # roles=lti_user.roles,
            # TODO - Set the context ID here
            context_id="testcourse",
            location=book_location,
        )
        self._sign_form_params(launch_url, launch_params)

        return (launch_url, launch_params)

    def _sign_form_params(self, url, params):
        client = oauthlib.oauth1.Client(
            self._oauth_key,
            self._oauth_secret,
            signature_method=SIGNATURE_HMAC_SHA1,
            signature_type=SIGNATURE_TYPE_BODY,
        )
        params.update(client.get_oauth_params(oauthlib.common.Request(url, "POST")))
        oauth_request = oauthlib.common.Request(url, "POST", body=params)
        params["oauth_signature"] = client.get_oauth_signature(oauth_request)
        return params

    def _launch_params(self, user_id, roles, context_id, location=None):
        # See https://developer.vitalsource.com/hc/en-us/articles/206156238-General-LTI-Usage
        params = {
            # User data. These should be proxied from the LTI launch.
            "user_id": user_id,
            "roles": roles,
            "context_id": context_id,
            # Static VitalSource launch parameters.
            "launch_presentation_document_target": "window",
            # Standard LTI launch parameters.
            "lti_version": "LTI-1p0",
            "lti_message_type": "basic-lti-launch-request",
        }

        if location:
            params["custom_book_location"] = location

        return params
