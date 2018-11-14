from lms.util import get_password_hash


class TestPasswordHash:
    def test_recreate_hash(self):
        password = "asdf"
        expected_hashed = (
            "e46df2a5b4d50e259b5154b190529483a5f8b7aaaa22a50447e377d33792577a"
            "".encode("utf8")
        )
        salt = "fbe82ee0da72b77b"

        actual_hash, _ = get_password_hash.get_hash(password, salt)

        assert expected_hashed == actual_hash

    def test_wrong_salt(self):
        password = "asdf"
        expected_hashed = (
            "e46df2a5b4d50e259b5154b190529483a5f8b7aaaa22a50447e377d33792577a"
            "".encode("utf8")
        )
        salt = "wrooongSaaaaalt"

        actual_hash, _ = get_password_hash.get_hash(password, salt)

        assert expected_hashed != actual_hash

    def test_wrong_password(self):
        password = "wrongPassword"
        expected_hashed = (
            "e46df2a5b4d50e259b5154b190529483a5f8b7aaaa22a50447e377d33792577a"
            "".encode("utf8")
        )
        expected_salt = "fbe82ee0da72b77b"

        actual_hash, _ = get_password_hash.get_hash(password, expected_salt)

        assert expected_hashed != actual_hash

    def test_unique_salts(self):
        cnt = 10
        password = "asdf"

        salts = list()
        for _ in range(cnt):
            _, salt = get_password_hash.get_hash(password)
            assert salt not in salts
            salts.append(salt)
