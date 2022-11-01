# Configuration

## Non-environment variable configuration

### The LMS user in `h`

For LMS to be able to communicate with `h` it needs a user with a matching
authority. For the moment this is manually entered into the DB e.g.

```sql
INSERT INTO public.user 
    (username, authority)
VALUES
    ('lms', 'lms.eg.hypothes.is')
```

### `h`'s `CLIENT_RPC_ALLOWED_ORIGINS`

In order to allow the client to talk to LMS, you must append the LMS's URL to
the `h` instance which is serving the client from Via. e.g.

```
CLIENT_RPC_ALLOWED_ORIGINS=https://lms.eg.hypothes.is
```

## Basic environment variables

The following environment variables are required for the basic operation of
LMS. Each of these is mandatory to get the service working correctly.

| Name                              | Example                                | Notes                                           | 
|-----------------------------------|----------------------------------------|-------------------------------------------------|
| `ADMIN_AUTH_GOOGLE_CLIENT_ID`     | `abcdef012.apps.googleusercontent.com` | An OAuth2 pair from Google for `/admin` pages   |
| `ADMIN_AUTH_GOOGLE_CLIENT_SECRET` | `01234567-89ab-cdef-0123-456789abcdef` | The matching secret from the above              |
| `DATABASE_URL`                    | `postgresql://user:pw@host/lms`        | Postgres DSN of this service main DB            | 
| `H_FDW_DATABASE_URL`              | `postgresql://user:pw@host/h`          | Postgres DSN pointing to H's DB                 | 
| `H_API_URL_PRIVATE`               | `https://cloud.hosting.url/api`        | URL for service to service communication        |
| `H_API_URL_PUBLIC`                | `https://fr.hypothes.is/api`           | URL for client to service communication         |
| `H_AUTHORITY`                     | `lms.eg.hypothes.is`                   | An authority to separate LMS annotations in `h` |
| `H_CLIENT_ID`                     | `fedcba98-7654-3210-fedc-ba9876543210` | A `client_credentials` OAuth2 pair from `h`     |
| `H_CLIENT_SECRET`                 | `0123456789abcdefghijklmnopqrABCDEFGH` | A `client_credentials` OAuth2 pair from `h`     |
| `H_JWT_CLIENT_ID`                 | `fedcba98-7654-3210-fedc-ba9876543210` | A `jwt_bearer` OAuth2 pair from `h`             |
| `H_JWT_CLIENT_SECRET`             | `0123456789abcdefghijklmnopqrABCDEFGH` | A `jwt_bearer` OAuth2 pair from `h`             |
| `JWT_SECRET`                      | `random-string-12345`                  | An arbitrary secret value                       |
| `JSTOR_API_SECRET`                | `random-string-12345`                  | JWT secret for authenticating with JSTOR        |
| `JSTOR_API_URL`                   | `http://example.com/api`               | URL of JSTOR API base url.                      |
| `LMS_SECRET`                      | `random-string-12345`                  | An arbitrary secret value                       |
| `OAUTH2_STATE_SECRET`             | `random-string-12345`                  | An arbitrary secret value                       |
| `RPC_ALLOWED_ORIGINS`             | `https://fr.hypothes.is`               | `h` instances clients can be connecting from    |
| `SESSION_COOKIE_SECRET`           | `random-string-12345`                  | An arbitrary secret value                       |
| `VIA_SECRET`                      | `matching-string-from-via`             | Must match the shared secret from Via           |
| `VIA_URL`                         | `https://via9.hypothes.is/`            | The matching Via                                |

See also:

 * [Getting H credentials](getting-h-credentials.md) - For `H_*_CLIENT_*`
 * [Getting Google credentials](getting-google-credentials.md) - `For ADMIN_AUTH_GOOGLE_CLIENT_*`

## Reporting / monitoring environment variables

The following environment variables are required for monitoring purposes. If 
you don't supply these variables the specific form of monitoring will not work.

| Name                    | Example                            | Notes                       | 
|-------------------------|------------------------------------|-----------------------------|
| `NEW_RELIC_APP_NAME`    | `lms`                              |                             | 
| `NEW_RELIC_ENVIRONMENT` | `prod`                             |                             |
| `NEW_RELIC_LICENSE_KEY` | `abcdefghijklmnopqrstuvwxyzabcdef` |                             |
| `SENTRY_DSN_FRONTEND`   | `https://abcdef123@sentry.io/1234` | Sentry DSN for the frontend |
| `SENTRY_DSN`            | `https://abcdef123@sentry.io/1234` | Sentry DSN for the backend  |
| `SENTRY_ENVIRONMENT`    | `prod`                             |                             |


### Getting New Relic credentials

_To be completed_

### Getting Sentry credentials

_To be completed_

## File integration environment variables

These variables are required to support each particular type of file source in
the file picker. If you don't supply these variables the specific file source 
will not work.

| Name                              | Type             | Example                                | Notes                                       | 
|-----------------------------------|------------------|----------------------------------------|---------------------------------------------|
| `BLACKBOARD_API_CLIENT_ID`        | Blackboard files | `01234567-89ab-cdef-0123-456789abcdef` | Provided by Blackboard                      |
| `BLACKBOARD_API_CLIENT_SECRET`    | Blackboard files | `0123456789abcdefghijklmnopqrstuv`     | Provided by Blackboard                      |
| `GOOGLE_CLIENT_ID`                | Google Drive     | `abcdef012.apps.googleusercontent.com` | A client ID from an OAuth2 key from Google  |
| `GOOGLE_DEVELOPER_KEY`            | Google Drive     | `01234567-89ab-cdef-0123-456789abcdef` | A developer key from Google                 |
| `ONEDRIVE_CLIENT_ID`              | MS OneDrive      | `01234567-89ab-cdef-0123-456789abcdef` | Developer key from Microsoft OneDrive       |
| `VITALSOURCE_API_KEY`             | VitalSource      | `0123456789ABCEDF`                     |                                             |

### Getting Blackboard credentials

_To be completed_

### Getting Google credentials

See [Getting Google credentials](getting-google-credentials.md).

### Getting OneDrive credentials

_To be completed_

You must update the redirect URL for the One Drive key you use to include your
target LMS environment. e.g.

`https://lms.eg.hypothes.is/onedrive/filepicker/redirect`

### Getting VitalSource credentials

_To be completed_
