import marshmallow


class LTIAuthParamsSchema(marshmallow.Schema):
    class Meta:
        unknown = marshmallow.EXCLUDE

    user_id = marshmallow.fields.Str(required=True)
    roles = marshmallow.fields.Str(required=True)
    tool_consumer_instance_guid = marshmallow.fields.Str(required=True)
    lis_person_name_given = marshmallow.fields.Str(load_default="")
    lis_person_name_family = marshmallow.fields.Str(load_default="")
    lis_person_name_full = marshmallow.fields.Str(load_default="")
    lis_person_contact_email_primary = marshmallow.fields.Str(load_default="")
