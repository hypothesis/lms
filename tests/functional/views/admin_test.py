import pytest


@pytest.mark.parametrize(
    "method,path",
    (
        # Create
        ("get", "/admin/instances/create"),
        ("post", "/admin/instances/create"),
        # Downgrade
        ("post", "/admin/instances/1234/downgrade"),
        # Move org
        ("post", "/admin/instances/1234/move_org"),
        # Search
        ("get", "/admin/instances/"),
        ("post", "/admin/instances/"),
        # Show
        ("get", "/admin/instances/1234/"),
        # Update
        ("post", "/admin/instances/1234/"),
        # Upgrade
        ("get", "/admin/instances/upgrade"),
        ("post", "/admin/instances/upgrade"),
    ),
)
def test_admin_authentication_redirects_to_google(app, method, path):
    response = getattr(app, method)(path)

    assert response.status_code == 302
    assert response.location.startswith("http://localhost/googleauth/login")
