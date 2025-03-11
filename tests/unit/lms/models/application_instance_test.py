from unittest.mock import sentinel

import pytest
from sqlalchemy.exc import IntegrityError

from lms.models import ApplicationInstance, ApplicationSettings, Family
from lms.models.json_settings import SettingFormat
from tests import factories


class TestApplicationSettings:
    def test_it(self):
        settings_fields_keys = [
            (s.group, s.key, s.compound_key, s.format)
            for s in ApplicationSettings.fields.values()
        ]

        assert settings_fields_keys == [
            (
                "blackboard",
                "files_enabled",
                "blackboard.files_enabled",
                SettingFormat.BOOLEAN,
            ),
            (
                "blackboard",
                "groups_enabled",
                "blackboard.groups_enabled",
                SettingFormat.BOOLEAN,
            ),
            (
                "canvas",
                "sections_enabled",
                "canvas.sections_enabled",
                SettingFormat.BOOLEAN,
            ),
            (
                "canvas",
                "groups_enabled",
                "canvas.groups_enabled",
                SettingFormat.BOOLEAN,
            ),
            ("canvas", "files_enabled", "canvas.files_enabled", SettingFormat.BOOLEAN),
            (
                "canvas",
                "folders_enabled",
                "canvas.folders_enabled",
                SettingFormat.BOOLEAN,
            ),
            (
                "canvas",
                "strict_section_membership",
                "canvas.strict_section_membership",
                SettingFormat.BOOLEAN,
            ),
            ("canvas", "pages_enabled", "canvas.pages_enabled", SettingFormat.BOOLEAN),
            (
                "canvas_studio",
                "admin_email",
                "canvas_studio.admin_email",
                SettingFormat.STRING,
            ),
            (
                "canvas_studio",
                "client_id",
                "canvas_studio.client_id",
                SettingFormat.STRING,
            ),
            (
                "canvas_studio",
                "client_secret",
                "canvas_studio.client_secret",
                SettingFormat.AES_SECRET,
            ),
            ("canvas_studio", "domain", "canvas_studio.domain", SettingFormat.STRING),
            (
                "desire2learn",
                "client_id",
                "desire2learn.client_id",
                SettingFormat.STRING,
            ),
            (
                "desire2learn",
                "client_secret",
                "desire2learn.client_secret",
                SettingFormat.AES_SECRET,
            ),
            (
                "desire2learn",
                "groups_enabled",
                "desire2learn.groups_enabled",
                SettingFormat.BOOLEAN,
            ),
            (
                "desire2learn",
                "files_enabled",
                "desire2learn.files_enabled",
                SettingFormat.BOOLEAN,
            ),
            (
                "google_drive",
                "files_enabled",
                "google_drive.files_enabled",
                SettingFormat.BOOLEAN,
            ),
            (
                "microsoft_onedrive",
                "files_enabled",
                "microsoft_onedrive.files_enabled",
                SettingFormat.BOOLEAN,
            ),
            ("moodle", "api_token", "moodle.api_token", SettingFormat.AES_SECRET),
            (
                "moodle",
                "groups_enabled",
                "moodle.groups_enabled",
                SettingFormat.BOOLEAN,
            ),
            ("moodle", "files_enabled", "moodle.files_enabled", SettingFormat.BOOLEAN),
            ("moodle", "pages_enabled", "moodle.pages_enabled", SettingFormat.BOOLEAN),
            ("vitalsource", "enabled", "vitalsource.enabled", SettingFormat.BOOLEAN),
            (
                "vitalsource",
                "user_lti_param",
                "vitalsource.user_lti_param",
                SettingFormat.STRING,
            ),
            (
                "vitalsource",
                "user_lti_pattern",
                "vitalsource.user_lti_pattern",
                SettingFormat.STRING,
            ),
            ("vitalsource", "api_key", "vitalsource.api_key", SettingFormat.STRING),
            (
                "vitalsource",
                "student_pay_enabled",
                "vitalsource.student_pay_enabled",
                SettingFormat.BOOLEAN,
            ),
            ("jstor", "enabled", "jstor.enabled", SettingFormat.BOOLEAN),
            ("jstor", "site_code", "jstor.site_code", SettingFormat.STRING),
            ("youtube", "enabled", "youtube.enabled", SettingFormat.BOOLEAN),
            ("hypothesis", "notes", "hypothesis.notes", SettingFormat.STRING),
            (
                "hypothesis",
                "auto_assigned_to_org",
                "hypothesis.auto_assigned_to_org",
                SettingFormat.BOOLEAN,
            ),
            (
                "hypothesis",
                "instructor_email_digests_enabled",
                "hypothesis.instructor_email_digests_enabled",
                SettingFormat.BOOLEAN,
            ),
            (
                "hypothesis",
                "lti_13_sourcedid_for_grading",
                "hypothesis.lti_13_sourcedid_for_grading",
                SettingFormat.BOOLEAN,
            ),
        ]


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
