def test_admin_authentication_redirects_to_google(app):
    response = app.get("/admin/instances/")

    assert response.status_code == 302
    assert response.location.startswith("http://localhost/googleauth/login")
