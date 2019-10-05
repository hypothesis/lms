Setting up Google Drive integration manually
============================================

If you're setting up the LMS app in a development environment you can just run
`make devdata` to do all this automatically. But if you're setting it up in a
production environment then you'll need to set up the Google Drive integration
manually.

The outcome of this process will be a configured Google project and valid
values for the `GOOGLE_APP_ID`, `GOOGLE_DEVELOPER_KEY` and `GOOGLE_CLIENT_ID`
environment variables.

1. Sign in to the [Google Developer Console](https://console.developers.google.com/apis/)
1. Create a new project. Set the `GOOGLE_APP_ID` environment variable to the ID for this project.
1. Navigate to the "Credentials" section
1. Generate an API key

    Use the "Create Credentials" option to generate an API key — retain this
    for the `GOOGLE_DEVELOPER_KEY` environment variable

1. Generate an OAuth client ID.

    Again, use the "Create Credentials" option to generate an OAuth client ID.

    This process involves a few steps (via web forms). The resulting ID string
    can be used as the value for the `GOOGLE_CLIENT_ID` environment variable.

    As of June, 2018, you'll need to create a "consent screen" before you can
    generate any OAuth client IDs — enter sensible values in the form fields
    here.

    For the OAuth client ID form itself:

    * Set application type to `Web Application`
    * The 'Authorized Javascript Origins' list should be edited to include the
      URL of the app (e.g. `https://lms.hypothes.is`).
    * The Authorized redirect URIs tab can be left blank

1. Enable the needed APIs.

    Head to the "Library" section of the Google developer console and enable:

    * Google Drive API
    * Google Picker API
