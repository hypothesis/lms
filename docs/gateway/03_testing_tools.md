# Testing tools

In order to help you start quickly and to aid with testing / debugging we
provide a number of Python based tools.

These tools also provide a reference implementation, which you can adapt to
your language / situation. They are **not** indended to be used outside of
testing and no warranty of guarantee of operation is given for them.

## Getting started

The tools are in this repository in [bin/gateway](../../bin/gateway). You can
access them by checking out the repository from Github:

```shell
git checkout git@github.com:hypothesis/lms.git
```

In order to use them you will need Python 3 installed. We recommend using a
[virtual environment](https://virtualenv.pypa.io/en/latest/) to install the
dependencies required, although a full guide is outside the scope of this
document.

One you have a suitable environment you can install the requirements with a
[tool like `pip`](https://pip.pypa.io/en/stable/installation/) as follows:

```shell
cd lms/bin/gateway
pip install -r requirements.txt
```

You should then be able to run the commands:

```shell
python oauth_call.py
```

## `oauth_call.py` - Calling the Gateway 

[The `oauth_call.py` script](../../bin/gateway/oauth_call.py) can be used to
make an OAuth1 signed POST request to an end-point such as the Gateway.

It requires a JSON configuration file which specifies the client key and shared
secret, as well as details of the URL and LTI parameters to pass. An example is
given in [`bin/gateway/gateway_qa_example.json`](../../bin/gateway/gateway_qa_example.json).

You will need to customize the values in this file to match your required
settings. You can read the [API Specification](02_api_spec.md) to see the required
fields. We will assume you have a file called `gateway.json` with the correct
values.

### Examples

```shell
./oauth_call.py --spec gateway.json
```

You should see JSON return values. You can supress extra debug info with
`--quiet` if you like:

```shell
./oauth_call.py --quiet --spec gateway.json
```

Debug information is routed to STDERR, whereas the reponse data is routed to
STDOUT, which allows you to view each separately:

```shell
./oauth_call.py --spec gateway.json 1>response.txt 2>errors.txt
```

## `h_call.py` - Calling the `h` API using Gateway data 

[The `oauth_call.py` script](../../bin/gateway/h_call.py) can make calls to the 
`h` API using the format returned by the Gateway end-point.

It can read those values from a JSON file, or directly from `oauth_call.py`. 
You can use this to make authenticated calls using an exchanged token and to
store a list of tests calls in a file.

### Examples

By default `h_call.py` just lists the calls that are available, but doesn't 
call any of them. Here we use an example file to provide a call.

```shell
./h_call.py --spec config/h_calls_qa.json
```
```shell
Available end-points:
	 * profile
```
We can use the name of these end-points to make a call:

```shell
./h_call.py --spec config/h_calls_qa.json --call profile
```

As we are not authenticated we will get default anonymous user info back.

### Examples combining with `oauth_call.py`

We can read the spec details directly from the `oauth_call.py` script instead 
of using JSON:

```shell
./oauth_call.py --quiet --spec gateway.json | ./h_call.py --stdin --call list_endpoints
```

We can combine this with automatic token exchange, and our predefined JSON 
calls to call the profile end-point again, but as the user we specified in 
our `gateway.json` config:

```shell
./oauth_call.py --quiet --spec gateway.json | ./h_call.py --stdin --spec config/h_calls_qa.json --authenticate --call profile
```

You should now see user specific details. As this is a bit long winded, short
codes are provided for each command. This is the same command as above:

```shell
./oauth_call.py -qs gateway.json | ./h_call.py -ais config/h_calls_qa.json -c profile
```

Using this method you can keep a list of pre-prepared calls to the `h` API in
a file and conveniently call them with the correct authentication for testing.