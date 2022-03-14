import pytest
import sqlalchemy.exc

from lms.models import GradingInfo


class TestGradingInfo:
    def test_it_persists_and_returns_attrs(
        self, application_instance, db_session, grading_info
    ):
        db_session.add(grading_info)
        lrs = db_session.query(GradingInfo).one()

        assert lrs.lis_result_sourcedid == "result_sourcedid"
        assert lrs.lis_outcome_service_url == "https://somewhere.else"
        assert lrs.application_instance_id == application_instance.id
        assert lrs.user_id == "339483948"
        assert lrs.context_id == "random context"
        assert lrs.resource_link_id == "random resource link id"
        assert lrs.tool_consumer_info_product_family_code == "MyFakeLTITool"
        assert lrs.h_username == "ltiuser1"
        assert lrs.h_display_name == "My Fake LTI User"

    @pytest.mark.parametrize(
        "non_nullable_field",
        [
            "lis_result_sourcedid",
            "lis_outcome_service_url",
            "application_instance_id",
            "user_id",
            "context_id",
            "resource_link_id",
            "h_username",
            "h_display_name",
        ],
    )
    def test_it_enforces_non_nullable_field_presence(
        self, db_session, grading_info, non_nullable_field
    ):
        setattr(grading_info, non_nullable_field, None)
        db_session.add(grading_info)
        with pytest.raises(
            sqlalchemy.exc.IntegrityError,
            match=f'null value in column "{non_nullable_field}" violates not-null constraint',
        ):
            db_session.flush()

    def test_it_enforces_uniqueness_constraint(
        self, grading_info, grading_info_duplicate, db_session
    ):
        db_session.add(grading_info)
        db_session.add(grading_info_duplicate)

        with pytest.raises(
            sqlalchemy.exc.IntegrityError,
            match="duplicate key value violates unique constraint",
        ):
            db_session.flush()

    @pytest.fixture
    def grading_info(self, grading_info_params):
        return GradingInfo(**grading_info_params)

    @pytest.fixture
    def grading_info_duplicate(self, grading_info_params):
        return GradingInfo(
            **dict(
                grading_info_params,
                lis_result_sourcedid="result_sourcedid_another",
                lis_outcome_service_url="https://somewhere.else_yet",
            )
        )

    @pytest.fixture
    def grading_info_params(self, application_instance):
        return {
            "lis_result_sourcedid": "result_sourcedid",
            "lis_outcome_service_url": "https://somewhere.else",
            "application_instance_id": application_instance.id,
            "user_id": "339483948",
            "context_id": "random context",
            "resource_link_id": "random resource link id",
            "tool_consumer_info_product_family_code": "MyFakeLTITool",
            "h_username": "ltiuser1",
            "h_display_name": "My Fake LTI User",
        }
