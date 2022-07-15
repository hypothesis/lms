# LMS Gateway


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

## Getting started

The Gateway is only available to certain partners. If you are interested in 
using the Gateway, please contact [Hypothesis support](https://web.hypothes.is/help/)
who can discuss your use case, and enable it for you.

We also provide a set of [testing tools](04_testing_tools.md) which should 
allow you to experiment with the API without having to write any code. A Python
environment and some setup is required to use these tools.

## See also

 * [Hypothesis API Specification](https://h.readthedocs.io/en/latest/api-reference/) - Details of the main `h` API
 * [Gateway API Specification](02_api_spec.md) - Details of the Gateway end-points used to gain access to the `h` API
 * [Authentication](03_authentication.md) - How to authenticate with the Gateway and `h` API
 * [Testing tools](04_testing_tools.md) - Testing tools and reference implementation
