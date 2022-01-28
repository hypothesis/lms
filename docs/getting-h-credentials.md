# Getting H credentials

If you're setting up the LMS app in a development environment you can just run
`make devdata` to do all this automatically. But if you're setting it up in a
production environment then you'll need to create the authclients and
environment variables necessary to integrate the LMS app with h manually.

## Create a `client_credentials` OAuth client in h

The LMS app requires the OAuth 2.0 `client_id` and `client_secret` from a
`client_credentials` type auth client in h in order to use certain h APIs, such
as the API for creating users.

Log in to your instance of h as an admin user. If you don't have an admin user 
account for your instance of h see
[Accessing the admin interface](http://h.readthedocs.io/en/latest/developing/administration/)
in the h docs.

* e.g. `http://<YOUR_H_INSTANCE>/login`

Go to `<YOUR_H_INSTANCE>/admin/oauthclients/new` and create an auth
client with these settings:

| Key          | Value                |
|--------------|----------------------|
| Name         | `LMS`                |
| Authority    | `lms.hypothes.is`    |
| Grant type   | `client_credentials` |
| Redirect URL | (Leave empty)        |

Click `Register client` and **keep the tab open** because you'll need the 
generated `Client ID` and `Client secret` for setting your environment 
variables later.

## Create a `jwt_bearer` OAuth client in h

The LMS app also requires the `client_id` and `client_secret` from a
`jwt_bearer` type auth client in h in order to generate authorization grant
tokens for logging in to h user accounts.

Go to `<YOUR_H_INSTANCE>/admin/oauthclients/new` and create an auth
client with these settings:

| Key          | Value             |
|--------------|-------------------|
| Name         | `LMS JWT`         |
| Authority    | `lms.hypothes.is` |
| Grant type   | `jwt_bearer`      |
| Redirect URL | (Leave empty)     |

Click `Register client` and **keep the tab open** because you'll need the 
generated `Client ID` and `Client secret` for setting your environment 
variables later.

## More on environment variables

For detailed instructions on the environment variables see 
[Configuration](configuration.md).