# Getting Google credentials

If you're setting up the LMS app in a development environment you can just run
`make devdata` to do all this automatically. But if you're setting it up in a
production environment then you'll need to set up the Google Drive integration
manually.

The outcome of this process will be a configured Google project and valid
values for the `GOOGLE_APP_ID`, `GOOGLE_DEVELOPER_KEY` and `GOOGLE_CLIENT_ID`
environment variables.

## For Google Drive

### Create "API Key"

1. Sign in to the [Google Developer Console](https://console.developers.google.com/apis/)
1. Use the `lms-prod` / `lms-qa` project etc. 
1. Navigate to the "Credentials" section
1. Generate an "API Key"

    Use the "Create Credentials" option to generate an API key — retain this
    for the `GOOGLE_DEVELOPER_KEY` environment variable

### Create "OAuth 2.0 Client ID"

Again, use the "Create Credentials" option to generate an OAuth client ID.

This process involves a few steps (via web forms). The resulting ID string
can be used as the value for the `GOOGLE_CLIENT_ID` environment variable.

For the OAuth client ID form:

* Set application type to `Web Application`
* The 'Authorized Javascript Origins' list should be edited to include the
  URL of the app (e.g. `https://lms.hypothes.is`).
* The Authorized redirect URIs tab can be left blank

### Add a consent screen

As of June, 2018, you'll need to create a "consent screen" before you can
generate any OAuth client IDs — enter sensible values in the form fields
here.

### Enable the needed APIs.

Head to the "Library" section of the Google developer console and enable:

* Google Drive API
* Google Picker API

## For the Admin Pages

For the `ADMIN_AUTH_GOOGLE_CLIENT_ID` and `ADMIN_AUTH_GOOGLE_CLIENT_SECRET`
environment variables follow the same instructions above to create an OAuth 2 
credential, but in the `lms-admin` project.

Make sure to setup the redirect URL like: 
`https://lms.hypothes.is/googleauth/login/callback`.

## More on environment variables

For detailed instructions on the environment variables see 
[Configuration](configuration.md).