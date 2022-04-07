from lms.views.lti.jwk import jwks


def test_jwks(rsa_key_service, pyramid_request):
    result = jwks(pyramid_request)

    rsa_key_service.get_all_public_jwks.assert_called_once_with()
    assert result == {"keys": rsa_key_service.get_all_public_jwks.return_value}
