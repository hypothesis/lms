Creating data and settings manually
===================================

If you're setting up the LMS app in a development environment you can just run
`make devdata` to do all this automatically. But if you're setting it up in a
production environment then you'll need to create the authclients and
environment variables necessary to integrate the LMS app with h manually.

**See also:** [Setting up Google Drive integration manually](google-drive.md)

## Setting up h integration manually

### Create a client_credentials auth client in h

The LMS app requires the OAuth 2.0 `client_id` and `client_secret` from a
`client_credentials`-type auth client in h in order to use certain h APIs, such
as the API for creating users.

To create the necessary auth client in h:

1. Log in to your instance of h as an admin user.

   If you don't have an admin user account for your instance of h see
   [Accessing the admin interface](http://h.readthedocs.io/en/latest/developing/administration/)
   in the h docs.

1. Go to `<YOUR_H_INSTANCE>/admin/oauthclients/new` and create an auth
   client with these settings:

   <dl>
     <dt>Name</dt>
     <dd>LMS</dd>
     <dt>Authority</dt>
     <dd>lms.hypothes.is</dd>
     <dt>Grant type</dt>
     <dd>client_credentials</dd>
     <dt>Redirect URL</dt>
     <dd>(Leave empty)</dd>
   </dl>

   Click <samp>Register client</samp> and **keep the tab open** because you'll
   need the generated <samp>Client ID</samp> and <samp>Client secret</samp> for
   setting your environment variables later.

### Create a jwt_bearer auth client in h

The LMS app also requires the `client_id` and `client_secret` from a
`jwt_bearer`-type auth client in h in order to generate authorization grant
tokens for logging in to h user accounts.

Go to `<YOUR_H_INSTANCE>/admin/oauthclients/new` and create an auth
client with these settings:

   <dl>
     <dt>Name</dt>
     <dd>LMS JWT</dd>
     <dt>Authority</dt>
     <dd>lms.hypothes.is</dd>
     <dt>Grant type</dt>
     <dd>jwt_bearer</dd>
     <dt>Redirect URL</dt>
     <dd>(Leave empty)</dd>
   </dl>

Click <samp>Register client</samp> and **keep the tab open** because you'll
need the generated <samp>Client ID</samp> and <samp>Client secret</samp> for
setting your environment variables later.

### Set environment variables

The LMS app requires several environment variables to be set. Set the following
environment variables in your shell. Notice that:

* You need to replace the `H_CLIENT_ID`, `H_CLIENT_SECRET`, `H_AUTHORITY`,
  `H_JWT_CLIENT_ID` and `H_JWT_CLIENT_SECRET` values below with the ones you
  generated in your h instance, when you
  were following the instructions above to create auth clients in h.
* We're going to use dummy values for certain required environment variables
  just to get the app to start up. Those features will not be working
  correctly. Below we'll link to docs for setting up those features correctly.

      # The values for H_CLIENT_ID, H_CLIENT_SECRET, H_AUTHORITY, H_JWT_CLIENT_ID
      # and H_JWT_CLIENT_SECRET should come from the auth clients that you
      # created in h earlier.
      export H_CLIENT_ID="232c***5121"
      export H_CLIENT_SECRET="eVJ4***rXkk"
      export H_AUTHORITY="lms.hypothes.is"
      export H_JWT_CLIENT_ID="3ac7***71e4"
      export H_JWT_CLIENT_SECRET="OJGx***c8x4"

      # This sets the password for the /reports page to "password".
      export USERNAME=jeremy
      export HASHED_PW=dc68***cc9f
      export SALT=eaea...72a2

      export VIA_URL="<YOUR_VIA_INSTANCE>"
      export JWT_SECRET="<YOUR_SECRET_STRING>"
      export LMS_SECRET="<ANOTHER_SECRET_STRING>"
      export H_API_URL_PUBLIC="<YOUR_H_INSTANCE>/api/"
      export H_API_URL_PRIVATE="<YOUR_H_INSTANCE>/api/"
      export RPC_ALLOWED_ORIGINS="<YOUR_H_INSTANCE>"
