from lms.models import RSAKey


class TestRSAKey:
    def test_kid(self, db_session):
        rsa_key = RSAKey()
        # Add to the session and commit to force the model's `default`
        db_session.add(rsa_key)
        db_session.commit()

        assert rsa_key.kid
        assert isinstance(rsa_key.kid, str)
        assert len(rsa_key.kid) == 32
