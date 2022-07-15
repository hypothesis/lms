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

## Calling the gateway with `oauth_call.py`

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