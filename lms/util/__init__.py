# -*- coding: utf-8 -*-
from lms.util.associate_user import associate_user
from lms.util.authenticate import authenticate
from lms.util.authorize_lms import authorize_lms, save_token
from lms.util.canvas_api import canvas_api, GET, POST
from lms.util.exceptions import UtilError, MissingOAuthConsumerKeyError, MissingUserIDError
from lms.util.h import generate_display_name, generate_username, generate_provider_unique_id
from lms.util.jwt import jwt
from lms.util.lti_launch import lti_launch
from lms.util.view_renderer import view_renderer

__all__ = (
    'associate_user',
    'authenticate',
    'authorize_lms',
    'canvas_api',
    'generate_display_name',
    'generate_username',
    'generate_provider_unique_id',
    'jwt',
    'lti_launch',
    'save_token',
    'view_renderer',
    'GET',
    'POST',
    'UtilError',
    'MissingOAuthConsumerKeyError',
    'MissingUserIDError',
)
