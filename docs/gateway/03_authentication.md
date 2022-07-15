# Authentication

Authentication happens in two steps:

 * In the first step you will perform the signed OAuth1 request to the Gateway
 * In the second step you will use tokens to authenticate with the `h` API

## Getting started

In order to authenticate with the Gateway you will need:

 * The tool consumer instance GUID of the LMS instance
 * The client key created when Hypothesis was installed
 * The shared secret created when Hypothesis was installed

If you do not know any of these values you can work with 
[Hypothesis support](https://web.hypothes.is/help/) to get the correct values.

## Calling the Gateway

> _Note: [See the `oauth_call.py` tool](04_testing_tools.md) for a demonstration 
this process._

You will need to make an OAuth1 signed post request. This involves adding 
certain extra OAuth specific fields to the form data, cryptographically signing
those parameters with the client secret and then making a conventional POST
request to the [Gateway end-point](02_api_spec.md).

The process is described in the [LTI 1.1 Implementation Guide](https://www.imsglobal.org/specs/ltiv1p1p1/implementation-guide#toc-4).

We also provide some [testing tools / reference implementation](04_testing_tools.md)
in Python. These tools are intended to get you started quickly after which you 
can adapt the implementation.

**Note:** There is a terminology difference  between OAuth1 and the LTI spec:

| This document     | LTI                     | OAuth1          | 
|-------------------|-------------------------|-----------------|
| `consumer_key`    | `oauth_consumer_key`    | `client_key`    |
| `consumer_secret` | `oauth_consumer_secret` | `client_secret` |

## Swapping the grant token for an access token

> _Note: [See the `h_call.py` tool](04_testing_tools.md) for a demonstration 
this process._

If you successfully call the Gateway end-point then the response you receive
will include a section called `h_api` which will list a number of pre-prepared
requests you can make.

One of these requests is called `grant_token_exchange` and provies the call you
need to make to get access tokens for the `h` API.

These are formatted so you can pass them directly to Python's 
[`requests` library](https://requests.readthedocs.io/en/latest/), (but the same
details can be used with any HTTP library). For example:

```python
from requests import Session
 
gateway_response = ...  # The response data from the Gateway end-point 
response = Session().request(**gateway_response['h_api']['grant_token_exchange'])
print(response.json())
```
This will return you a set of OAuth2 credentials you can use with the `h` API. 
e.g.

```json
{
    "access_token": "5218-fV8jIXVx3-NOT-A-REAL-TOKEN-6645AcJGbWiJJss",
    "expires_in": 3600.0,
    "token_type": "Bearer",
    "refresh_token": "4344-k2RMSX23-NOT-A-REAL-TOKEN-DHj4UYk8nsBvKP4"
}
```

## Using the OAuth 2 access

You can then use the access token in future requests to the `h` API by 
including a header like this (using the value you received):

```
Authorization: Bearer 5218-fV8jIXVx3-NOT-A-REAL-TOKEN-6645AcJGbWiJJss
```

You can also perform OAuth2 token refreshes to keep access tokens alive, and 
prevent you from having to perform this step each time.

By combining this token, URL and header details provided and the 
[Hypothesis API Specification](https://h.readthedocs.io/en/latest/api-reference/) 
you should be able to make any calls you need to the `h` API.