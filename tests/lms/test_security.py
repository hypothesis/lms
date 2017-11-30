from lms import security


class TestSecurityPassword(object):
    def test_correct_password(self):
        salt = 'fbe82ee0da72b77b'
        password = 'asdf'
        expected_hash = 'e46df2a5b4d50e259b5154b190529483a5f8b7aaaa22a50447e377d33792577a'

        assert security.check_password(password, expected_hash, salt)

    def test_wrong_password(self):
        salt = 'fbe82ee0da72b77b'
        #password = 'asdf'
        wrong_password = 'wrooong'
        expected_hash = 'e46df2a5b4d50e259b5154b190529483a5f8b7aaaa22a50447e377d33792577a'

        assert not security.check_password(wrong_password, expected_hash, salt)

    def test_wrong_salt(self):
        #salt = 'fbe82ee0da72b77b'
        wrong_salt = 'nopenope'
        password = 'asdf'
        expected_hash = 'e46df2a5b4d50e259b5154b190529483a5f8b7aaaa22a50447e377d33792577a'

        assert not security.check_password(password, expected_hash, wrong_salt)


class TestSecurityGroupFinder:
    def test_find_group(self, pyramid_request):
        userid = 'report_viewers'
        groups = security.groupfinder(userid, pyramid_request)

        assert groups is not None
        assert 'report_viewers' in groups

    def test_not_find_group(self, pyramid_request):
        userid = 'wrongid'

        groups = security.groupfinder(userid, pyramid_request)

        assert groups is None
