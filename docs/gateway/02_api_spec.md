# API Specification

## Base URLs

All end-points here are specified with reference to these base URLs:

| Environment       | URL                           | Usage                                  |
|-------------------|-------------------------------|----------------------------------------|
| Local development | `http://localhost:5000/`      | Local product development              | 
| QA                | `https://qa-lms.hypothes.is/` | Publicly available testing environment |
| Production        | `https://lms.hypothes.is/`    | Final deployment with real users       |

Unless you are familiar with Hypothesis development, we recommend you start 
with the public QA test environment.

## POST `/api/gateway/h/lti`

Returns connection details and contextual information about the current user,
course and optionally assignment.

### Headers
```
Accept: application/json
Content-Type: application/x-www-form-urlencoded
```

### Authentication

You will need to OAuth1 sign the parameters in order to pass authentication.
For details of how to do this see [Authentication](03_authentication.md).

### Post body fields

We accept any and all LTI 1.1 parameters.

 * See "Basic Launch Data" in https://www.imsglobal.org/specs/ltiv1p1p1/implementation-guide

It is recommended for stability and the best performance that you pass all LTI
parameters received onto this end-point. This will ensure compatibility as the
more features may be added in future which require fields which were previously
optional.

| Field                         | Example                    | Notes                                                                   |
|-------------------------------|----------------------------|-------------------------------------------------------------------------|
| `lti_version`                 | `LTI-1p0`                  | Specify LTI version (only 1.1 supported at present)                     |
| `lti_message_type`            | `basic-lti-launch-request` | Indicate you are making a launch                                        |
| `tool_consumer_instance_guid` | `ab5e8623477ffe8324`       | The unique ID for the tool consumer instance (e.g. Canvas installation) |
| `user_id`                     | `2978763`                  | The user id we should act on behalf of                                  |
| `roles`                       | `Instructor`               | The role that user has (used in permission generation)                  |
| `context_id`                  | `454`                      | Specify the course you want to access                                   |
| `context_title`               | `Course name`              | Specify the course name (used to update records)                        |
| `resource_link_id`            | `22`                       | _(optional)_ Narrow the scope to a single assignment                    |

### Responses

**200 - OK**

Everything worked correctly. You should receive a JSON payload which matches 
[this schema](schema.json) (in [JSON Schema](http://json-schema.org/) format).

This schema file also includes an example of the output you can expect.

**403 - Not authorized**

The authentication has failed. This might be due to:

 * Incorrect client key and shared secret
 * Incorrect signing
 * Using a client key and secret pair which are associated with another GUID

**422 - Unprocessable Entity**

Authentication was successful, but required fields were missing, or did not 
match the expected format.