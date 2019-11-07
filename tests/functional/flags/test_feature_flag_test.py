from tests.functional.base_class import TestBaseClass


class TestFeatureFlagTest(TestBaseClass):
    def test_we_can_set_a_feature_flag_via_param(self, app):
        # We aren't really running this test because we care, but just
        # to prove the testing framework
        result = app.get(
            "/flags/test", params=self.json_fixture("flags/bar_on.json"), status=200
        )

        assert result.json_body["bar"] == "Bar feature flag is enabled"
        assert result.json_body["foo"] == "Foo feature flag is disabled"
