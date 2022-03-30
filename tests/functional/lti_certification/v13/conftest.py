import jwt
import pytest

import importlib_resources


keys_path = importlib_resources.files("tests.functional.lti_certification.v13")
JWT_KID = "JWT_KEY_KID"


@pytest.fixture(scope="session")
def jwt_private_key():
    with open(keys_path / "jwt_private.key") as key:
        return key.read()


@pytest.fixture(scope="session")
def jwt_public_key():
    return open("./jwt_public.key")


@pytest.fixture
def jwt_headers():
    return {"kid": JWT_KID}


@pytest.fixture
def make_jwt(jwt_headers, jwt_private_key):
    def _make_jwt(payload, headers=None):
        if not headers:
            headers = jwt_headers

        return jwt.encode(payload, jwt_private_key, algorithm="RS256", headers=headers)

    return _make_jwt
