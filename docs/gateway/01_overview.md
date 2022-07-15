# LMS Gateway

_See also:_

 * [API Specification](02_api_spec.md) - Details of the end-points
 * [Testing tools](03_testing_tools.md) - Testing tools and reference implementation

## Overview

The LMS Gateway allows you to access the main Hypothesis (`h`) API to retrieve 
annotation and other data on behalf of and related to a certain user. 

It will also provide you with contextual information about the current LMS 
context in order to help you:

 * Ask for the right things from `h`
 * Map between LMS and `h` ids and concepts

### The current implementation is a work in progress

Details of the call structure, required fields and approach are likely to 
change at this time without warning.

### How it works

You can authenticate with the Gateway end-point using a standard LTI 1.1 basic 
launch: an OAuth1 signed POST request. LTI 1.3 is **_not_** supported at this
time. 

This will return to you a payload with:

 * Instructions to call the `h` API and tokens to authenticate with it
 * Contextual information about a course or assignment (users, groups, 
 assignments etc.)

You should then have everything you need to make any calls to the `h` API **as
the user you passed to us**. This means you will see what they can see, and can
act on behalf of that user.

## Authentication

Authentication happens in two steps:

 * In the first step you will perform the signed OAuth1 request to the Gateway
 * In the second step you will use tokens to authenticate with the `h` API

### Getting started

The Gateway is only available to certain partners. If you are interested in 
using the Gateway, please contact [Hypothesis support](https://web.hypothes.is/help/)
who can discuss your use case, and enable it for you.

In order to authenticate with the Gateway you will need:

 * The tool consumer instance GUID of the LMS instance
 * The client key created when Hypothesis was installed
 * The shared secret created when Hypothesis was installed

If you do not know any of these values you can work with 
[Hypothesis support](https://web.hypothes.is/help/) to get the correct values.

### Calling the gateway

You will need to make an OAuth1 signed post request. This involves adding 
certain extra OAuth specific fields to the form data, cryptographically signing
those parameters with the client secret and then making a conventional POST
request to the [Gateway end-point](02_api_spec.md).

The process is described in the [LTI 1.1 Implementation Guide](https://www.imsglobal.org/specs/ltiv1p1p1/implementation-guide#toc-4)

We also provide some [testing tools / reference implementation](03_testing_tools.md)
in Python. These tools are intended to get you started quickly after which you 
can adapt the implementation.

**Note:** There is a terminology difference  between OAuth1 and the LTI spec:

| This document     | LTI                     | OAuth1          | 
|-------------------|-------------------------|-----------------|
| `consumer_key`    | `oauth_consumer_key`    | `client_key`    |
| `consumer_secret` | `oauth_consumer_secret` | `client_secret` |