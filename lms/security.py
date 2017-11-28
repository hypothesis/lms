# from pyramid.authentication import AuthTktAuthenticationPolicy
# from pyramid.authorization import ACLAuthorizationPolicy
#
# from lms.models.user import User
#
#
# class MyAuthenticationPolicy(AuthTktAuthenticationPolicy):
#     def authenticated_userid(self, request):
#         user = request.user
#         if user is not None:
#             return user.id
#
#
# def get_user(request):
#     user_id = request.unauthenticated_userid
#     if user_id is not None:
#         user = request.dbsession.query(User).get(user_id)
#         return user

import bcrypt


# TODO: Move these functions to User model
def hash_password(pw):
    pwhash = bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
    return pwhash.decode('utf8')


def check_password(pw, hashed_pw):
    expected_hash = hashed_pw.encode('utf8')
    return bcrypt.checkpw(pw.encode('utf8'), expected_hash)


# USERS = {'editor': hash_password('editor'),
#          'viewer': hash_password('viewer')}
# GROUPS = {'editor': ['group:editors']}
# TODO: don't use these lists, find way to use User model
USERS = {'report_viewer': hash_password('report_viewer')}
GROUPS = {'report_viewer': ['group:report_viewers']}


def groupfinder(userid, request):
    if userid in USERS:
        return GROUPS.get(userid, [])
