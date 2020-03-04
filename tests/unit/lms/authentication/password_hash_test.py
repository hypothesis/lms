from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.authentication.password_hash import check_password, hash_password


class TestHashPassword:
    def test_it_generates_hash_as_expected(self):
        # Runs a real test without mocking pbkdf2_hmac. After this we mock
        # as aren't here to check pbkdf2_hmac works and it's very slow
        actual_hash, _ = hash_password("asdf", "fbe82ee0da72b77b")

        assert (
            actual_hash
            == "e46df2a5b4d50e259b5154b190529483a5f8b7aaaa22a50447e377d33792577a".encode(
                "utf8"
            )
        )

    def test_it_runs_pbkdf2_hmac_with_expected_settings(self, pbkdf2_hmac):
        hash_password(sentinel.password, sentinel.salt)

        pbkdf2_hmac.assert_called_once_with("sha256", Any(), Any(), 1_000_000)

    @pytest.mark.parametrize(
        "password,expected_password",
        [
            ["password", "password".encode("utf8")],
            ["utf8-password".encode("utf8"), "utf8-password".encode("utf8")],
        ],
    )
    def test_it_encodes_the_password_correctly(
        self, password, expected_password, pbkdf2_hmac
    ):
        hash_password(password, sentinel.salt)

        pbkdf2_hmac.assert_called_once_with(Any(), expected_password, Any(), Any())

    @pytest.mark.parametrize(
        "salt,expected_salt",
        [
            ["salt", "salt".encode("utf8")],
            ["utf8-salt".encode("utf8"), "utf8-salt".encode("utf8")],
        ],
    )
    def test_it_encodes_the_salt_correctly(self, salt, expected_salt, pbkdf2_hmac):
        _, returned_salt = hash_password(sentinel.password, salt)

        pbkdf2_hmac.assert_called_once_with(Any(), Any(), expected_salt, Any())

        assert returned_salt == expected_salt

    @pytest.mark.usefixtures("pbkdf2_hmac")
    def test_it_generates_random_salt_with_no_salt(self):
        _, salt_1 = hash_password(sentinel.password)
        _, salt_2 = hash_password(sentinel.password)

        assert salt_1
        assert salt_1 != salt_2

    @pytest.fixture
    def pbkdf2_hmac(self, patch):
        pbkdf2_hmac = patch("lms.authentication.password_hash.pbkdf2_hmac")
        pbkdf2_hmac.return_value = b"somebytes"
        return pbkdf2_hmac


class TestCheckPassword:
    correct_hash = "some very long hash"

    @pytest.mark.parametrize(
        "provided_hash,success", [[correct_hash, True], ["anything else", False]]
    )
    def test_we_compare_hashes(self, provided_hash, success):
        assert check_password("password", provided_hash, "salt") == success

    def test_wrong_password(self):
        salt = "fbe82ee0da72b77b"
        # password = 'asdf'
        wrong_password = "wrooong"
        expected_hash = (
            "e46df2a5b4d50e259b5154b190529483a5f8b7aaaa22a50447e377d33792577a"
        )

        assert not check_password(wrong_password, expected_hash, salt)

    def test_wrong_salt(self):
        # salt = 'fbe82ee0da72b77b'
        wrong_salt = "nopenope"
        password = "asdf"
        expected_hash = (
            "e46df2a5b4d50e259b5154b190529483a5f8b7aaaa22a50447e377d33792577a"
        )

        assert not check_password(password, expected_hash, wrong_salt)

    # Assuming the tests above pass, we can mock out the hash_password function
    @pytest.fixture(autouse=True)
    def hash_password(self, patch):
        hash_password = patch("lms.authentication.password_hash.hash_password")
        hash_password.return_value = self.correct_hash.encode("utf8"), sentinel.salt
        return hash_password
