class TestSanity:
    """Some basic tests to ensure the world exists etc."""

    def test_sanity(self, app):
        app.get("/not_a_url_at_all", status=404)

    def test_we_can_read_and_send_params(self, app):
        # We aren't really running this test because we care, but just
        # to prove the testing framework
        result = app.get("/flags/test", params={"feature_flags.bar": True}, status=200)

        assert result.json_body["bar"] == "Bar feature flag is enabled"
        assert result.json_body["foo"] == "Foo feature flag is disabled"
