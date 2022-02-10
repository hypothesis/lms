"""Schema for validating LTI launch params."""

import marshmallow

from lms.models import LTIUser, display_name
from lms.validation._base import PyramidRequestSchema

__all__ = ("OpenIDAuthSchema",)


class OpenIDAuthSchema(PyramidRequestSchema):
    location = "form"

    # TODO I don't know if the same schema could:
    # - Validate that the request has the required raw params
    # - Validate that the params in the "envelope" are correct

    # state = marshmallow.fields.Str(required=True)
    # authenticity_token = marshmallow.fields.Str(required=True)
    # id_token = marshmallow.fields.Str(required=True)

    user_id = marshmallow.fields.Str(required=True)
    roles = marshmallow.fields.Str(required=True)
    tool_consumer_instance_guid = marshmallow.fields.Str(required=True)
    lis_person_name_given = marshmallow.fields.Str(load_default="")
    lis_person_name_family = marshmallow.fields.Str(load_default="")
    lis_person_name_full = marshmallow.fields.Str(load_default="")
    lis_person_contact_email_primary = marshmallow.fields.Str(load_default="")

    oauth_consumer_key = marshmallow.fields.Str(required=True)

    def __init__(self, request):
        super().__init__(request)

    def lti_user(self):
        """
        Return an models.LTIUser from the request's launch params.

        :raise ValidationError: if the request isn't a valid LTI launch request

        :rtype: LTIUser
        """
        kwargs = self.parse(location="form")

        return LTIUser(
            user_id=kwargs["user_id"],
            oauth_consumer_key=kwargs["oauth_consumer_key"],
            roles=kwargs["roles"],
            tool_consumer_instance_guid=kwargs["tool_consumer_instance_guid"],
            display_name=display_name(
                kwargs["lis_person_name_given"],
                kwargs["lis_person_name_family"],
                kwargs["lis_person_name_full"],
            ),
            email=kwargs["lis_person_contact_email_primary"],
        )

    @marshmallow.pre_load
    def _decode_jwt(self, data, **_kwargs):
        id_token = data["id_token"]

        # TODO move this _jwt
        # TODO actually validate the JWT
        import jwt
        from jwt import PyJWKClient

        jwks_client = PyJWKClient(
            "https://canvas.instructure.com/api/lti/security/jwks"
        )
        # signing_key = jwks_client.get_signing_key_from_jwt(id_token)
        jwt_params = jwt.decode(
            id_token,
            # key=signing_key.key,
            options={"verify_signature": False},  # TODO
        )
        data["roles"] = ",".join(
            jwt_params["https://purl.imsglobal.org/spec/lti/claim/roles"]
        )
        data["user_id"] = jwt_params["sub"]
        data["tool_consumer_instance_guid"] = jwt_params[
            "https://purl.imsglobal.org/spec/lti/claim/tool_platform"
        ]["guid"]
        data["user_id"] = jwt_params["sub"]

        data["lis_person_name_given"] = jwt_params["given_name"]
        data["lis_person_name_family"] = jwt_params["family_name"]
        data["lis_person_name_full"] = jwt_params["name"]
        data["lis_person_contact_email_primary"] = jwt_params["email"]

        # TODO BIG TODO
        # data["oauth_consumer_key"] = "Hypothesisb3be0b33d0b5e4b1cf3aaf04e0e1819a" canvas
        data["oauth_consumer_key"] = jwt_params[
            "oauth_consumer_key"
        ] = "Hypothesis14af0fe87c9deb2e461f88be4a8d5364"  # BB

        self.context["request"].jwt_params = jwt_params

        return data
