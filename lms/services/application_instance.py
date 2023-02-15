import secrets
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from logging import getLogger
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.exc import NoResultFound

from lms.db import BASE, full_text_match
from lms.models import ApplicationInstance, JSONSettings, LTIParams, LTIRegistration
from lms.services.aes import AESService
from lms.services.exceptions import SerializableError
from lms.services.organization import OrganizationService
from lms.validation import ValidationError

LOG = getLogger(__name__)


class ApplicationInstanceNotFound(Exception):
    """The requested ApplicationInstance wasn't found in the database."""


class AccountDisabled(SerializableError):
    """Indicate that we have disabled this account through it's org."""

    def __init__(self, application_instance: ApplicationInstance):
        super().__init__(
            message="Account has been disabled",
            error_code="account_disabled",
            details={
                "organization_id": application_instance.organization.public_id,
                "application_instance_id": application_instance.id,
            },
        )


@dataclass
class SearchBuilder:
    base_model: BASE
    clause_builders: dict
    key_map: dict = field(default_factory=lambda: {"id_": "id", "type_": "type"})
    query_start: Optional[callable] = None

    def get_query(self, db_session, kwargs, combination=sa.and_):
        query = self.query_start(db_session) or db_session.query(self.base_model)

        return self.filter_query(query, kwargs, combination=combination)

    def filter_query(self, query, kwargs, combination=sa.and_):
        if clauses := list(self.get_clauses(kwargs)):
            query = query.filter(combination(*clauses))

        return query

    def get_clauses(self, kwargs):
        for key, value in kwargs.items():
            clause = self.get_clause(key, value)
            # Watch out as real clauses can be falsy when evaluated
            if clause is not None:
                yield clause

    def get_clause(self, key, value):
        if value is None:
            return

        key = self.key_map.get(key, key)

        if mapper := self.clause_builders.get(key):
            return mapper(value)

        if hasattr(self.base_model, key):
            return getattr(self.base_model, key) == value

        raise ValueError(f"Can't map '{key}'")

    def builds(self, key=None):
        def builds(function):
            self.clause_builders[key or function.__name__] = function
            return function

        return builds


_SEARCH_BUILDER = SearchBuilder(
    ApplicationInstance,
    query_start=lambda db_session: db_session.query(ApplicationInstance).outerjoin(
        LTIRegistration
    ),
    clause_builders={
        "issuer": lambda value: LTIRegistration.issuer == value,
        "client_id": lambda value: LTIRegistration.client_id == value,
        "name": lambda value: full_text_match(ApplicationInstance.name, value),
        "settings": lambda value: JSONSettings.matching(
            ApplicationInstance.settings, value
        ),
        "organization_public_id": lambda value: ApplicationInstance.organization.has(
            public_id=value
        ),
    },
)


@_SEARCH_BUILDER.builds("email")
def _filter_by_email(value):
    return sa.or_(
        sa.func.lower(field) == value.lower()
        if "@" in value
        else field.ilike(f"%@{value}")
        for field in (
            ApplicationInstance.requesters_email,
            ApplicationInstance.tool_consumer_instance_contact_email,
        )
    )


class ApplicationInstanceService:
    def __init__(
        self,
        db,
        request,
        aes_service: AESService,
        organization_service: OrganizationService,
    ):
        self._db = db
        self._request = request
        self._aes_service = aes_service
        self._organization_service = organization_service
        self._search_builder = _SEARCH_BUILDER

    @lru_cache(maxsize=1)
    def get_current(self) -> ApplicationInstance:
        """
        Return the current request's `ApplicationInstance`.

        This is the `ApplicationInstance` with `id` matching
        `request.application_instance_id`.

        :raises ApplicationInstanceNotFound: if there's no matching
            `ApplicationInstance`
        :raise AccountDisabled: If the organization associated with this
            instance is disabled
        """
        if self._request.lti_user and self._request.lti_user.application_instance_id:
            application_instance = self.get_by_id(
                self._request.lti_user.application_instance_id
            )

            # Check to see if this application instance belongs to a disabled
            # organization.
            if (
                application_instance
                and (org := application_instance.organization)
                and not org.enabled
            ):
                LOG.info(
                    "Account access was blocked for application_instance=%s org=%s",
                    application_instance.id,
                    org.id,
                )
                raise AccountDisabled(application_instance)

            return application_instance

        raise ApplicationInstanceNotFound()

    @lru_cache(maxsize=1)
    def get_by_id(self, id_) -> ApplicationInstance:
        try:
            return self._ai_search_query(id_=id_).one()
        except NoResultFound as err:
            raise ApplicationInstanceNotFound() from err

    @lru_cache(maxsize=128)
    def get_by_consumer_key(self, consumer_key) -> ApplicationInstance:
        """
        Return the `ApplicationInstance` with the given `consumer_key`.

        :param consumer_key: Consumer key to search by
        :raise ApplicationInstanceNotFound: if there's no matching
            `ApplicationInstance`
        """
        if not consumer_key:
            raise ApplicationInstanceNotFound()

        try:
            return self._ai_search_query(consumer_key=consumer_key).one()
        except NoResultFound as err:
            raise ApplicationInstanceNotFound() from err

    @lru_cache(maxsize=128)
    def get_by_deployment_id(
        self, issuer: str, client_id: str, deployment_id: str
    ) -> ApplicationInstance:
        if not all([issuer, client_id, deployment_id]):
            raise ApplicationInstanceNotFound()

        try:
            return (
                self._db.query(ApplicationInstance)
                .join(LTIRegistration)
                .filter(
                    LTIRegistration.issuer == issuer,
                    LTIRegistration.client_id == client_id,
                    ApplicationInstance.deployment_id == deployment_id,
                )
                .one()
            )
        except NoResultFound as err:
            raise ApplicationInstanceNotFound() from err

    def search(
        self,
        *,
        id_=None,
        name=None,
        consumer_key=None,
        issuer=None,
        client_id=None,
        deployment_id=None,
        tool_consumer_instance_guid=None,
        limit=100,
        email=None,
        settings=None,
        organization_public_id=None,
    ) -> List[ApplicationInstance]:
        """Return the instances that match all of the passed parameters."""

        return (
            self._ai_search_query(
                id_=id_,
                name=name,
                consumer_key=consumer_key,
                issuer=issuer,
                client_id=client_id,
                deployment_id=deployment_id,
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                email=email,
                settings=settings,
                organization_public_id=organization_public_id,
            )
            .order_by(
                ApplicationInstance.last_launched.desc().nulls_last(),
                ApplicationInstance.updated.desc(),
            )
            .limit(limit)
            .all()
        )

    def _ai_search_query(self, **kwargs):
        return self._search_builder.get_query(self._db, kwargs)

    def update_application_instance(  # pylint:disable=too-many-arguments
        self,
        application_instance,
        name=None,
        lms_url=None,
        deployment_id=None,
        developer_key=None,
        developer_secret=None,
        organization_public_id=None,
    ):
        if name:
            application_instance.name = name

        if lms_url:
            application_instance.lms_url = lms_url

        if deployment_id:
            application_instance.deployment_id = deployment_id

        if developer_key:
            application_instance.developer_key = developer_key

        if developer_secret:
            aes_iv = self._aes_service.build_iv()
            encrypted_secret = self._aes_service.encrypt(aes_iv, developer_secret)
            application_instance.aes_cipher_iv = aes_iv
            application_instance.developer_secret = encrypted_secret

        if organization_public_id:
            org = self._organization_service.get_by_public_id(organization_public_id)
            if org:
                application_instance.organization = org
            else:
                raise ValidationError(
                    messages={
                        "organization_public_id": [
                            f"Organization {organization_public_id} not found"
                        ]
                    }
                )

    def create_application_instance(  # pylint:disable=too-many-arguments
        self,
        lms_url,
        email,
        developer_key,
        developer_secret,
        organization_public_id,
        name,
        deployment_id=None,
        lti_registration_id=None,
    ) -> ApplicationInstance:
        """Create an application instance."""
        consumer_key = (
            "Hypothesis" + secrets.token_hex(16) if not deployment_id else None
        )

        application_instance = ApplicationInstance(
            name=name,
            consumer_key=consumer_key,
            shared_secret=secrets.token_hex(32),
            lms_url=lms_url,
            requesters_email=email,
            created=datetime.utcnow(),
            # Some helpful defaults for settings
            settings={
                "canvas": {
                    "sections_enabled": False,
                    "groups_enabled": bool(developer_key),
                }
            },
            deployment_id=deployment_id,
            lti_registration_id=lti_registration_id,
        )
        # If either one of developer_key or developer_secret is missing,
        # then we won't set either on creation
        if not all([developer_secret, developer_key]):
            developer_key = developer_secret = None

        self.update_application_instance(
            application_instance,
            developer_key=developer_key,
            developer_secret=developer_secret,
            organization_public_id=organization_public_id,
        )
        self._db.add(application_instance)
        self._db.flush()  # Force the returned AI to have an ID

        return application_instance

    def update_from_lti_params(self, application_instance, params: LTIParams):
        """
        Update all the LMS-related attributes present in `params`.

        If the current instance already has a `tool_consumer_instance_guid`
        report it on logging and don't update any of the columns.
        """

        tool_consumer_instance_guid = params.get("tool_consumer_instance_guid")
        if not tool_consumer_instance_guid:
            # guid identifies the rest of the LMS data, if not there skip any
            # updates
            return

        application_instance.check_guid_aligns(tool_consumer_instance_guid)

        # Make sure this application instance is associated with an org.
        self._organization_service.auto_assign_organization(application_instance)

        for attr in [
            "tool_consumer_info_product_family_code",
            "tool_consumer_instance_description",
            "tool_consumer_instance_url",
            "tool_consumer_instance_name",
            "tool_consumer_instance_contact_email",
            "tool_consumer_instance_guid",
            "tool_consumer_info_version",
            "custom_canvas_api_domain",
        ]:
            setattr(application_instance, attr, params.get(attr))

        # This is a potentially misleading, as we can get here from deep-linked
        # "launches". Depending on whether you count that as a launch or not.
        application_instance.last_launched = datetime.now()


def factory(_context, request):
    return ApplicationInstanceService(
        db=request.db,
        request=request,
        aes_service=request.find_service(AESService),
        organization_service=request.find_service(OrganizationService),
    )
