# Getting H credentials

If you're setting up the LMS app in a development environment you can just run
`make devdata` to do all this automatically. But if you're setting it up in a
production environment then you'll need to create the authclients and
environment variables necessary to integrate the LMS app with h manually.

## Create a client_credentials auth client in h

The LMS app requires the OAuth 2.0 `client_id` and `client_secret` from a
`client_credentials`-type auth client in h in order to use certain h APIs, such
as the API for creating users.

To create the necessary auth client in h:


1. Log in to your instance of h as an admin user.
   If you don't have an admin user account for your instance of h see
   [Accessing the admin interface](http://h.readthedocs.io/en/latest/developing/administration/)
   in the h docs.
   * e.g. `http://<YOUR_H_INSTANCE>/login`

2. Go to `<YOUR_H_INSTANCE>/admin/oauthclients/new` and create an auth
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

## Create a jwt_bearer auth client in h

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

## More on environment variables

For detailed instructions on the environment variables see 
[Configuration](configuration.md).