from unittest.mock import sentinel

import pytest
from sqlalchemy.exc import IntegrityError

from lms.models import ApplicationInstance, Family
from tests import factories


class TestApplicationInstance:
    def test_it_persists_application_instance(self, db_session):
        initial_count = db_session.query(ApplicationInstance).count()

        factories.ApplicationInstance()

        new_count = db_session.query(ApplicationInstance).count()
        assert new_count == initial_count + 1

    def test_provisioning_defaults_to_True(self, application_instance, db_session):
        db_session.flush()

        assert application_instance.provisioning is True

    def test_provisioning_can_be_disabled(self, application_instance, db_session):
        application_instance.provisioning = False
        db_session.flush()

        assert not application_instance.provisioning

    def test_provisioning_is_not_nullable(self, db_session, application_instance):
        application_instance.provisioning = None

        db_session.flush()

        assert application_instance.provisioning is not None

    def test_settings_can_be_retrieved(self, application_instance):
        application_instance.settings = {"group": {"key": "value"}}

        assert application_instance.settings.get("group", "key") == "value"

    def test_can_update_settings(self, application_instance):
        application_instance.settings = {"group": {"key": "value"}}

        application_instance.settings.set("group", "key", "new_value")

        assert application_instance.settings["group"]["key"] == "new_value"

    def test_consumer_key_cant_be_null(self, db_session, application_instance):
        application_instance.consumer_key = None

        with pytest.raises(IntegrityError, match="consumer_key"):
            db_session.flush()

    def test_shared_secret_cant_be_null(self, db_session, application_instance):
        application_instance.shared_secret = None

        with pytest.raises(IntegrityError, match="shared_secret"):
            db_session.flush()

    def test_lms_url_cant_be_null(self, db_session, application_instance):
        application_instance.lms_url = None

        with pytest.raises(IntegrityError, match="lms_url"):
            db_session.flush()

    def test_requesters_email_cant_be_null(self, db_session, application_instance):
        application_instance.requesters_email = None

        with pytest.raises(IntegrityError, match="requesters_email"):
            db_session.flush()

    def test_lms_host(self, application_instance):
        application_instance.lms_url = "https://example.com/lms/"

        assert application_instance.lms_host() == "example.com"

    @pytest.mark.parametrize("lms_url", ["", "foo", "https://example[.com/foo"])
    def test_lms_host_raises_ValueError(self, application_instance, lms_url):
        application_instance.lms_url = lms_url

        with pytest.raises(ValueError):  # noqa: PT011
            application_instance.lms_host()

    def test_decrypted_developer_secret_returns_the_decrypted_developer_secret(
        self, application_instance, aes_service
    ):
        application_instance.developer_secret = sentinel.developer_secret
        application_instance.aes_cipher_iv = sentinel.aes_cipher_iv

        developer_secret = application_instance.decrypted_developer_secret(aes_service)

        aes_service.decrypt.assert_called_once_with(
            application_instance.aes_cipher_iv, application_instance.developer_secret
        )
        assert developer_secret == aes_service.decrypt.return_value

    def test_decrypted_developer_secret_returns_None_if_ApplicationInstance_has_no_developer_secret(
        self, application_instance, aes_service
    ):
        application_instance.developer_secret = None

        assert application_instance.decrypted_developer_secret(aes_service) is None

    @pytest.mark.parametrize(
        "lti_registration_id,deployment_id,lti_version",
        [
            (None, None, "LTI-1p0"),
            (None, "deployment_id", "LTI-1p0"),
            (1, None, "LTI-1p0"),
            (1, "deployment_id", "1.3.0"),
        ],
    )
    def test_lti_version(
        self, lti_registration_id, deployment_id, lti_version, application_instance
    ):
        application_instance.lti_registration_id = lti_registration_id
        application_instance.deployment_id = deployment_id

        assert application_instance.lti_version == lti_version

    @pytest.mark.parametrize(
        "family_code,family",
        [
            ("BlackboardLearn", Family.BLACKBOARD),
            ("canvas", Family.CANVAS),
            ("BlackbaudK12", Family.BLACKBAUD),
            ("desire2learn", Family.D2L),
            ("moodle", Family.MOODLE),
            ("schoology", Family.SCHOOLOGY),
            ("sakai", Family.SAKAI),
            ("wut", Family.UNKNOWN),
            ("", Family.UNKNOWN),
            (None, Family.UNKNOWN),
        ],
    )
    def test_family(self, application_instance, family_code, family):
        application_instance.tool_consumer_info_product_family_code = family_code

        assert application_instance.family == family

    @pytest.fixture
    def application_instance(self):
        """Return an ApplicationInstance with minimal required attributes."""
        return factories.ApplicationInstance()
