from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.models.public_id import InvalidPublicId, PublicId
from lms.models.region import Region


class TestPublicId:
    def test_it_generates_ids(self):
        public_id = PublicId(
            region=Region(code="us", authority="lms.hypothes.is"),
            model_code="code",
        )

        assert public_id.instance_id == Any.string.matching(r"[A-Za-z0-9-_]{22}")

    def test_generate_instance_id(self):
        assert PublicId.generate_instance_id() == Any.string.matching(
            r"[A-Za-z0-9-_]{22}"
        )

    def test_parse(self):
        region = Region(code="us", authority="lms.hypothes.is")
        public_id = PublicId.parse(
            "us.APP_CODE.MODEL_CODE.INSTANCE_ID",
            expect_model_code="MODEL_CODE",
            expect_region=region,
        )

        assert isinstance(public_id, PublicId)
        assert public_id.region == region
        assert public_id.model_code == "MODEL_CODE"
        assert public_id.app_code == "APP_CODE"
        assert public_id.instance_id == "INSTANCE_ID"

    @pytest.mark.parametrize("bad_value", ("too.few", "too.many.dots.in.this"))
    def test_parse_raises_with_bad_dots(self, bad_value):
        with pytest.raises(InvalidPublicId):
            PublicId.parse(
                bad_value,
                expect_model_code=sentinel.expect_model_code,
                expect_region=sentinel.expect_region,
            )

    def test_parse_raises_with_bad_region(self):
        with pytest.raises(InvalidPublicId):
            PublicId.parse(
                "NOT_A_REGION_CODE.lms.model.id",
                expect_model_code="model",
                expect_region=Region(code="ca", authority="lms.ca.hypothes.is"),
            )

    @pytest.mark.parametrize(
        "kwargs",
        (
            {"expect_model_code": "not_model"},
            {"expect_region": Region(code="ca", authority="lms.ca.hypothes.is")},
        ),
    )
    def test_parse_raises_with_expectations_missed(self, kwargs):
        kwargs.setdefault("expect_model_code", "model")
        kwargs.setdefault(
            "expect_region", Region(code="us", authority="lms.hypothes.is")
        )
        with pytest.raises(InvalidPublicId):
            PublicId.parse("us.lms.model.id", **kwargs)

    def test___str__(self, public_id):
        assert str(public_id) == "us.APP_CODE.MODEL_CODE.INSTANCE_ID"

    @pytest.fixture
    def public_id(self):
        return PublicId(
            region=Region(code="us", authority="lms.hypothes.is"),
            model_code="MODEL_CODE",
            app_code="APP_CODE",
            instance_id="INSTANCE_ID",
        )
