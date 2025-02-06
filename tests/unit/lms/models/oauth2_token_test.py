import datetime

import pytest
import sqlalchemy.exc

from lms.models import OAuth2Token
from lms.models.oauth2_token import Service


class TestOAuth2Token:
    def test_persist_and_retrieve_all_attrs(self, application_instance, db_session):
        now = datetime.datetime.utcnow()  # noqa: DTZ003

        # Add a token with the default "lms" service
        db_session.add(
            OAuth2Token(
                user_id="test_user_id",
                application_instance_id=application_instance.id,
                access_token="test_access_token",  # noqa: S106
                refresh_token="test_refresh_token",  # noqa: S106
                expires_in=3600,
                received_at=now,
                service=Service.LMS,
            )
        )

        token = db_session.query(OAuth2Token).one()
        assert token.user_id == "test_user_id"
        assert token.application_instance_id == application_instance.id
        assert token.application_instance == application_instance
        assert token.access_token == "test_access_token"  # noqa: S105
        assert token.refresh_token == "test_refresh_token"  # noqa: S105
        assert token.expires_in == 3600
        assert token.received_at == now
        assert token.service == Service.LMS

        # Add a second token with a non-default service
        db_session.add(
            OAuth2Token(
                user_id="test_user_id",
                application_instance_id=application_instance.id,
                access_token="test_access_token",  # noqa: S106
                refresh_token="test_refresh_token",  # noqa: S106
                expires_in=3600,
                received_at=now,
                service=Service.CANVAS_STUDIO,
            )
        )
        token = (
            db_session.query(OAuth2Token).filter_by(service=Service.CANVAS_STUDIO).one()
        )
        assert token.service == Service.CANVAS_STUDIO

    @pytest.mark.parametrize("column", ["user_id", "access_token"])
    def test_columns_that_cant_be_None(self, db_session, init_kwargs, column):
        del init_kwargs[column]
        db_session.add(OAuth2Token(**init_kwargs))

        with pytest.raises(
            sqlalchemy.exc.IntegrityError, match=f'null value in column "{column}"'
        ):
            db_session.flush()

    def test_setting_application_instance_sets_fk(
        self, application_instance, db_session, init_kwargs
    ):
        del init_kwargs["application_instance_id"]
        init_kwargs["application_instance"] = application_instance
        token = OAuth2Token(**init_kwargs)
        db_session.add(token)
        db_session.flush()

        assert token.application_instance_id == application_instance.id

    def test_defaults(self, db_session, init_kwargs):
        token = OAuth2Token(**init_kwargs)
        db_session.add(token)

        db_session.flush()

        assert token.refresh_token is None
        assert token.expires_in is None
        assert isinstance(token.received_at, datetime.datetime)
        assert token.service == Service.LMS

    @pytest.fixture
    def init_kwargs(self, application_instance):
        """
        Return the **minimum** kwargs needed to init a valid OAuth2Token.

        No optional kwargs or kwargs with default values are included here.
        """
        return {
            "user_id": "test_user_id",
            "access_token": "test_access_token",
            "application_instance_id": application_instance.id,
        }
