import jwt


def build_jwt_from_lti_launch(lti_params, jwt_secret):
    """Build a client jwt token from lti_launch params."""
    data = {
        'user_id': lti_params['user_id'],
        'roles': lti_params['roles'],
        'consumer_key': lti_params['oauth_consumer_key'],
    }
    jwt_token = jwt.encode(data,
                           jwt_secret,
                           'HS256').decode('utf-8')
    return jwt_token
