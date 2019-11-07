class TestLandingPage:
    def test_we_can_get_the_page(self, app):
        result = app.get("/", status=200)

        assert "<html" in result
