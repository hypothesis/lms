class TestStatus:
    def test_it(self, app):
        result = app.get("/_status", status=200)

        assert result.content_type == "application/json"
        assert result.json == {"status": "okay"}
        assert (
            result.headers["Cache-Control"]
            == "max-age=0, must-revalidate, no-cache, no-store"
        )
