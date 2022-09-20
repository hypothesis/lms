import pytest
from h_matchers import Any

from lms.models.public_id import InvalidPublicId, PublicId
from lms.models.region import Regions


class TestPublicId:
    def test_it_generates_ids(self):
        public_id = PublicId(region=Regions.US, model_code="code")

        assert public_id.instance_id == Any.string.matching(r"[A-Za-z0-9-_]{22}")

    def test_generate_instance_id(self):
        assert PublicId.generate_instance_id() == Any.string.matching(
            r"[A-Za-z0-9-_]{22}"
        )

    def test_parse(self):
        public_id = PublicId.parse(
            "us.APP_CODE.MODEL_CODE.INSTANCE_ID", expect_app_code=None
        )

        assert isinstance(public_id, PublicId)
        assert public_id.region == Regions.US
        assert public_id.model_code == "MODEL_CODE"
        assert public_id.app_code == "APP_CODE"
        assert public_id.instance_id == "INSTANCE_ID"

    @pytest.mark.parametrize("bad_value", ("too.few", "too.many.dots.in.this"))
    def test_parse_raises_with_bad_dots(self, bad_value):
        with pytest.raises(InvalidPublicId):
            PublicId.parse(bad_value)

    def test_parse_raises_with_bad_region(self):
        with pytest.raises(InvalidPublicId):
            PublicId.parse("NOT_A_REGION_CODE.lms.model.id")

    @pytest.mark.parametrize(
        "expect,value",
        (
            ("expect_app_code", "not_lms"),
            ("expect_model_code", "not_model"),
            ("expect_region", Regions.CA),
        ),
    )
    def test_parse_raises_with_expectations_missed(self, expect, value):
        with pytest.raises(InvalidPublicId):
            PublicId.parse("us.lms.model.id", **{expect: value})

    def test___str__(self, public_id):
        assert str(public_id) == "us.APP_CODE.MODEL_CODE.INSTANCE_ID"

    def test___eq__(self, public_id):
        assert public_id == public_id
        assert public_id != PublicId(Regions.CA, model_code="different")
        assert public_id == "us.APP_CODE.MODEL_CODE.INSTANCE_ID"
        assert public_id != "us.APP_CODE.MODEL_CODE.different"

    @pytest.fixture
    def public_id(self):
        return PublicId(
            region=Regions.US,
            model_code="MODEL_CODE",
            app_code="APP_CODE",
            instance_id="INSTANCE_ID",
        )
