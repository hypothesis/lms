import datetime

import pytest
import sqlalchemy.exc

from lms.models import OAuth2Token


class TestOAuth2Token:
    def test_persist_and_retrieve_all_attrs(self, application_instance, db_session):
        now = datetime.datetime.utcnow()

        db_session.add(
            OAuth2Token(
                user_id="test_user_id",
                consumer_key=application_instance.consumer_key,
                application_instance_id=application_instance.id,
                access_token="test_access_token",
                refresh_token="test_refresh_token",
                expires_in=3600,
                received_at=now,
            )
        )

        token = db_session.query(OAuth2Token).one()
        assert token.user_id == "test_user_id"
        assert token.consumer_key == application_instance.consumer_key
        assert token.application_instance_id == application_instance.id
        assert token.application_instance == application_instance
        assert token.access_token == "test_access_token"
        assert token.refresh_token == "test_refresh_token"
        assert token.expires_in == 3600
        assert token.received_at == now

    def test_user_id_cant_be_None(self, db_session, init_kwargs):
        del init_kwargs["user_id"]
        db_session.add(OAuth2Token(**init_kwargs))

        with pytest.raises(
            sqlalchemy.exc.IntegrityError,
            match='null value in column "user_id" violates not-null constraint',
        ):
            db_session.flush()

    def test_setting_consumer_key_sets_application_instance(
        self, application_instance, db_session, init_kwargs
    ):
        token = OAuth2Token(**init_kwargs)
        db_session.add(token)
        db_session.flush()

        assert token.application_instance == application_instance

    def test_setting_application_instance_sets_fk(
        self, application_instance, db_session, init_kwargs
    ):
        del init_kwargs["application_instance_id"]
        init_kwargs["application_instance"] = application_instance
        token = OAuth2Token(**init_kwargs)
        db_session.add(token)
        db_session.flush()

        assert token.application_instance_id == application_instance.id

    def test_access_token_cant_be_None(self, db_session, init_kwargs):
        del init_kwargs["access_token"]
        db_session.add(OAuth2Token(**init_kwargs))

        with pytest.raises(
            sqlalchemy.exc.IntegrityError,
            match='null value in column "access_token" violates not-null constraint',
        ):
            db_session.flush()

    def test_refresh_token_defaults_to_None(self, db_session, init_kwargs):
        token = OAuth2Token(**init_kwargs)
        db_session.add(token)

        db_session.flush()

        assert token.refresh_token is None

    def test_expires_in_defaults_to_None(self, db_session, init_kwargs):
        token = OAuth2Token(**init_kwargs)
        db_session.add(token)

        db_session.flush()

        assert token.expires_in is None

    def test_received_at_defaults_to_now(self, db_session, init_kwargs):
        token = OAuth2Token(**init_kwargs)
        db_session.add(token)

        db_session.flush()

        assert isinstance(token.received_at, datetime.datetime)

    @pytest.fixture
    def init_kwargs(self, application_instance):
        """
        Return the **minimum** kwargs needed to init a valid OAuth2Token.

        No optional kwargs or kwargs with default values are included here.
        """
        return dict(
            user_id="test_user_id",
            access_token="test_access_token",
            consumer_key=application_instance.consumer_key,
            application_instance_id=application_instance.id,
        )
