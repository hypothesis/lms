import pytest


@pytest.mark.parametrize(
    "method,path",
    (
        # Create
        ("get", "/admin/instance/create"),
        ("post", "/admin/instance/create"),
        # Downgrade
        ("post", "/admin/instance/1234/downgrade"),
        # Move org
        ("post", "/admin/instance/1234/move_org"),
        # Search
        ("get", "/admin/instances/"),
        ("post", "/admin/instances/"),
        # Show
        ("get", "/admin/instance/1234/"),
        # Update
        ("post", "/admin/instance/1234/"),
        # Upgrade
        ("get", "/admin/instance/upgrade"),
        ("post", "/admin/instance/upgrade"),
    ),
)
def test_admin_authentication_redirects_to_google(app, method, path):
    response = getattr(app, method)(path)

    assert response.status_code == 302
    assert response.location.startswith("http://localhost/googleauth/login")
