from lms.models import ApplicationInstance
from lms.models import LTIUser as User
from lms.models import display_name as create_display_name


class UserService:
    def __init__(self, db, application_instance_service):
        self._db = db
        self._application_instance_service = application_instance_service

    def get(self, oauth_consumer_key, user_id):
        return (
            self._db.query(User)
            .join(ApplicationInstance)
            .filter(
                ApplicationInstance.oauth_consumer_key == oauth_consumer_key,
                User.user_id == user_id,
            )
            .one_or_none()
        )

    def upsert_from_lti(  # pylint: disable=too-many-arguments
        self,
        oauth_consumer_key,
        user_id,
        tool_consumer_instance_guid,
        roles=None,
        email=None,
        display_name=None,
        lis_person_name_given=None,
        lis_person_name_family=None,
        lis_person_name_full=None,
    ):

        user = self.get(oauth_consumer_key, user_id)

        if not display_name:
            display_name = create_display_name(
                lis_person_name_given,
                lis_person_name_family,
                lis_person_name_full,
            )

        if not user:
            ai = self._application_instance_service.get(oauth_consumer_key)
            user = User(
                user_id=user_id,
                oauth_consumer_key=oauth_consumer_key,
                application_instance=ai,
            )
            self._db.add(user)

        user.display_name = display_name
        user.email = email
        user.roles = roles
        user.tool_consumer_instance_guid = tool_consumer_instance_guid

        self._db.flush()

        return user


def factory(_context, request):
    return UserService(
        request.db,
        request.find_service(name="application_instance"),
    )
