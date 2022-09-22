import pytest
from h_matchers import Any

from lms.models.public_id import PublicId
from lms.models.region import Regions


class TestPublicId:
    def test_it_generates_ids(self):
        public_id = PublicId(region=Regions.US, model_code="code")

        assert public_id.instance_id == Any.string.matching(r"[A-Za-z0-9-_]{22}")

    def test_generate_instance_id(self):
        assert PublicId.generate_instance_id() == Any.string.matching(
            r"[A-Za-z0-9-_]{22}"
        )

    def test___str__(self, public_id):
        assert str(public_id) == "us.APP_CODE.MODEL_CODE.INSTANCE_ID"

    @pytest.fixture
    def public_id(self):
        return PublicId(
            region=Regions.US,
            model_code="MODEL_CODE",
            app_code="APP_CODE",
            instance_id="INSTANCE_ID",
        )
