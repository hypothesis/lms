from urllib.parse import urlencode

from jwt.algorithms import RSAAlgorithm
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config


@view_config(
    route_name="lti_oidc",
    request_method=("POST", "GET"),  ## BB get, canvas POST
    renderer="json",
)
def lti_oidc(request):
    # http://www.imsglobal.org/spec/security/v1p0/#step-2-authentication-request
    params = {
        "scope": "openid",
        "response_type": "id_token",
        "response_mode": "form_post",
        "prompt": "none",
        "client_id": request.params["client_id"],
        "redirect_uri": request.params["target_link_uri"],
        "state": "STATE",  # TODO
        "nonce": "NONCE",  # TODO
        "login_hint": request.params["login_hint"],
        "lti_message_hint": request.params["lti_message_hint"],
    }

    print(request.params)

    authorice_redirect_url = "https://canvas.instructure.com/api/lti/authorize_redirect"
    authorice_redirect_url = "https://developer.blackboard.com/api/v1/gateway/oidcauth"

    return HTTPFound(location=f"{authorice_redirect_url}?{urlencode(params)}")


private_key = {
    "p": "7WY5dxoFqavf1QVM9qXS-SZr48WBjnAV4guLlHh7y6wwPvjfEPyc7MWwAIaolmypI2sGKCZm7xftBBxCDtbcQxppBd-uvoW9gCTPENTUZpDNR0UYbR1lvi6dTyJfOzb2YJR_giF74DmOw8bpH2uO0OlLSMhTUXVT0faKqgOM4pk",
    "kty": "RSA",
    "q": "pVrSMDz_jxyWYK6VxrWiQgsD9QiAf8YC6EYQZlK7zh3_OxG4zDeAgWfaCTJ-pyWDo6hjieA4gMqcgI8pRtXkv8q1wY1JK1z1oerJ1RMzNMRkMWPPi9egcKKyvIEoUT6tAqhpXmxjnOXgSy0D5hIyB1xOt2n9U_NI-2d7mzu9wUc",
    "d": "NnSS-UYLet237zGCoIDeEhbKnrEUunXT1S5gg9l1vkuWDtNKna31CSiZ4_oYDvpcV0_DV50O3ZWQvpB8tb6iXs4cgEp91RLeW0RbwP1-vpv9PZjQV7rI1BJMz6MLxBEB_fKACEf6PjZBiel33BzAWXqX8A7Fwbzh2a4Lf-fmTF70aJZqZ9Dt8UkrJEJh2unM0QRzugv23t6nTneX-slkwcFAaiCPoyCGAduUa3gj6Bhkz7ZlOT9Id66U1ipfz-8yyvKILpTFSqae1lP5zQL8cNTsadUKXsLh7A9FR2Q9MwwERpeMdZ-n5BWSGF4fkp7m2JU1ZFT8sUWjC1528BkFoQ",
    "e": "AQAB",
    "kid": "a70262c4-181e-4d57-8056-d6d02a264284",
    "qi": "2SrXqyTFC2nZi9W0PUxsc9taCxDIrjYEtMdqmhrBEbFFdPJDkB1iI21GpZtTGERkNdy9Py7CKN5UrylrVzbWEECIHX_4JbMdXJEpqhikcS-MX55-1c6d5gbDjd3X424yCYvGW_znEw-OBLUpXyORLu5ekSMWUkP7XBJFfmwziB0",
    "dp": "hcj3F4SlrlG66Wx8S_91Xo1lfc3_TgsieenxtjET6trVsZdE9mi18sURg6pfda40v04AAT5rAdDk9E0MeRpitLo8d1_wNVRfT8junFikfkyaMtDgjBVmEgBpDICdVFyMCi-FkAtYqSsmpnQBSoCt0lO25oRmV-Cb5RZgXKF1kvk",
    "alg": "RS256",
    "dq": "lDARgJOaADqBdgHgTqXG1WMj17wX1Oqy_lCUL-9jSfROITTfpXz0GITmvSlYohkXoVquYgjk-l8Z5IjoWAgmqc9UFjK1aTw1EjflS6SaVmbO2Ah4Hv5OVcMpZZBmfnEqAeDGFY4Ts6-71ANypASYe0o5bVx6YHr-Y_g4qUTf6M8",
    "n": "mVcb5I6EOQi4Z2kFMR4lCNS8dUATfGMm3GiDUDUUIE8RS6swQQjlN72vZxuyZmi07755B9BgvFvCtni4rrUNJixXiaKpE_XrFKSKTJ0RiMCp76fOYG7hTJF3O5fZ42j6mUsEAyr9zV1AClQZUOVz2SN0pRCVxf8HC7lllwPfwLUXjkgHf8yBmffw_oAZLCgfWgRCS2AyzfMFMyxAsCx8gAFvYxroh47kAfR-Qy4No2GbUkbWbhEUZwwnHe-zgMoa1M_LMx8-_hZXjOlOGoDskoTWpZ9QDFWsC45-JlndGWkgnDqBF6F4BCY-jrvafeP4lRsW5O1ruwut_G6zwN0xbw",
}

public_key = {
    "kty": "RSA",
    "e": "AQAB",
    "kid": "a70262c4-181e-4d57-8056-d6d02a264284",
    "alg": "RS256",
    "n": "mVcb5I6EOQi4Z2kFMR4lCNS8dUATfGMm3GiDUDUUIE8RS6swQQjlN72vZxuyZmi07755B9BgvFvCtni4rrUNJixXiaKpE_XrFKSKTJ0RiMCp76fOYG7hTJF3O5fZ42j6mUsEAyr9zV1AClQZUOVz2SN0pRCVxf8HC7lllwPfwLUXjkgHf8yBmffw_oAZLCgfWgRCS2AyzfMFMyxAsCx8gAFvYxroh47kAfR-Qy4No2GbUkbWbhEUZwwnHe-zgMoa1M_LMx8-_hZXjOlOGoDskoTWpZ9QDFWsC45-JlndGWkgnDqBF6F4BCY-jrvafeP4lRsW5O1ruwut_G6zwN0xbw",
    "use": "sig",
}

from cryptography.hazmat.primitives import serialization

pem_private_key = RSAAlgorithm.from_jwk(private_key).private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption(),
)


@view_config(
    route_name="jwts",
    request_method="GET",
    renderer="json",
)
def jwts(request):
    # TODO either document how to generate from a private key
    # or take from env vars
    # or generate on startup
    return {"keys": [public_key]}
