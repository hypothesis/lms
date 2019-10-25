import pytest
import sqlalchemy.exc

from lms.models import ApplicationInstance, LISResultSourcedId


class TestLISResultSourcedId:
    def test_it_persists_and_returns_attrs(
        self, application_instance, db_session, lis_result_sourcedid
    ):
        db_session.add(lis_result_sourcedid)
        lrs = db_session.query(LISResultSourcedId).one()

        assert lrs.lis_result_sourcedid == "result_sourcedid"
        assert lrs.lis_outcome_service_url == "https://somewhere.else"
        assert lrs.oauth_consumer_key == application_instance.consumer_key
        assert lrs.user_id == "339483948"
        assert lrs.context_id == "random context"
        assert lrs.resource_link_id == "random resource link id"
        assert lrs.tool_consumer_info_product_family_code == "BlackboardLearn"
        assert lrs.h_username == "blackboarduser1"
        assert lrs.h_display_name == "Black Board User"

    @pytest.mark.parametrize(
        "non_nullable_field",
        [
            "lis_result_sourcedid",
            "lis_outcome_service_url",
            "oauth_consumer_key",
            "user_id",
            "context_id",
            "resource_link_id",
            "h_username",
            "h_display_name",
        ],
    )
    def test_it_enforces_non_nullable_field_presence(
        self, db_session, lis_result_sourcedid, non_nullable_field
    ):
        setattr(lis_result_sourcedid, non_nullable_field, None)
        db_session.add(lis_result_sourcedid)
        with pytest.raises(
            sqlalchemy.exc.IntegrityError,
            match=f'null value in column "{non_nullable_field}" violates not-null constraint',
        ):
            db_session.flush()

    def test_it_enforces_uniqueness_constraint(
        self, lis_result_sourcedid, lis_result_duplicate_sourcedid, db_session
    ):
        db_session.add(lis_result_sourcedid)
        db_session.add(lis_result_duplicate_sourcedid)

        with pytest.raises(
            sqlalchemy.exc.IntegrityError,
            match="duplicate key value violates unique constraint",
        ):
            db_session.flush()

    @pytest.fixture
    def application_instance(self, db_session):
        """The ApplicationInstance that the LISResultSourcedIds belong to"""
        application_instance = ApplicationInstance(
            consumer_key="test_consumer_key",
            shared_secret="test_shared_secret",
            lms_url="test_lms_url",
            requesters_email="test_requesters_email",
        )
        db_session.add(application_instance)
        return application_instance

    @pytest.fixture
    def lis_result_sourcedid(self, application_instance):
        return LISResultSourcedId(
            lis_result_sourcedid="result_sourcedid",
            lis_outcome_service_url="https://somewhere.else",
            oauth_consumer_key=application_instance.consumer_key,
            user_id="339483948",
            context_id="random context",
            resource_link_id="random resource link id",
            tool_consumer_info_product_family_code="BlackboardLearn",
            h_username="blackboarduser1",
            h_display_name="Black Board User",
        )

    @pytest.fixture
    def lis_result_duplicate_sourcedid(self, application_instance):
        return LISResultSourcedId(
            lis_result_sourcedid="result_sourcedid_another",
            lis_outcome_service_url="https://somewhere.else_yet",
            oauth_consumer_key=application_instance.consumer_key,
            user_id="339483948",
            context_id="random context",
            resource_link_id="random resource link id",
            tool_consumer_info_product_family_code="BlackboardLearn",
            h_username="blackboarduser1",
            h_display_name="Black Board User",
        )
