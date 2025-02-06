"""
Upgrade Canvas SSO URLs.

Canvas has upgraded the URLs used in LTI1.3 registrations.

The change is not mandatory or urgent but it should future proof the registrations.

See: https://community.canvaslms.com/t5/The-Product-Blog/Minor-LTI-1-3-Changes-New-OIDC-Auth-Endpoint-Support-for/ba-p/551677


Revision ID: 0c52a13c6cad
Revises: 1872d16c28a4
"""

from alembic import op

revision = "0c52a13c6cad"
down_revision = "1872d16c28a4"

# DB column, old URL, new URL
URLS = (
    # The OIDC Auth endpoint, also called the Authorization Redirect URL
    (
        "auth_login_url",
        "https://canvas.instructure.com/api/lti/authorize_redirect",
        "https://sso.canvaslms.com/api/lti/authorize_redirect",
    ),
    # The Canvas Public JWKs endpoint
    (
        "key_set_url",
        "https://canvas.instructure.com/api/lti/security/jwks",
        "https://sso.canvaslms.com/api/lti/security/jwks",
    ),
    # The Grant Host endpoint, sent as the aud claim in LTI Advantage API tokens
    (
        "token_url",
        "https://canvas.instructure.com/login/oauth2/token",
        "https://sso.canvaslms.com/login/oauth2/token",
    ),
)


def upgrade() -> None:
    conn = op.get_bind()

    for field, old_url, new_url in URLS:
        result = conn.execute(
            f"""
            UPDATE lti_registration
            SET {field} = '{new_url}'
            WHERE {field} ='{old_url}'
            """  # noqa: S608
        )
        print(f"\tUpdated lti_registration.{field}:", result.rowcount)  # noqa: T201


def downgrade() -> None:
    conn = op.get_bind()

    for field, old_url, new_url in URLS:
        result = conn.execute(
            f"""
            UPDATE lti_registration
            SET {field} = '{old_url}'
            WHERE {field} ='{new_url}'
            """  # noqa: S608
        )
        print(f"\tDowngraded lti_registration.{field}:", result.rowcount)  # noqa: T201
