#!/usr/bin/env python

"""
Call an LTI style OAuth1 end-point using a JSON definition file.

See `docs/gateway/03_testing_tools.md` for more details.
"""

import json
import random
import sys
import time
from argparse import ArgumentParser
from datetime import datetime

import oauthlib.common
import oauthlib.oauth1
from requests import Session

parser = ArgumentParser(description="A tool for making LTI style OAuth 1 POST requests")
parser.add_argument(
    "--spec", "-s", required=True, help="Load call definition from a JSON file"
)
parser.add_argument(
    "--quiet", "-q", action="store_const", const=True, help="No debug output"
)


class OAuthSession:
    """Make OAuth1 authenticated calls to an end-point."""

    def __init__(self, consumer_key, shared_secret):
        super().__init__()

        self._consumer_key = consumer_key
        self._oauth_client = oauthlib.oauth1.Client(
            client_key=consumer_key, client_secret=shared_secret
        )
        self._session = Session()

    def post(self, url, data, **kwargs):
        return self._session.post(url, data=self._sign_post_data(url, data), **kwargs)

    def _sign_post_data(self, url, data):
        data.update(
            {
                "oauth_consumer_key": self._consumer_key,
                "oauth_callback": "about:blank",
                "oauth_nonce": "".join(random.choices("0123456789abcdef", k=64)),
                "oauth_signature_method": "HMAC-SHA1",
                "oauth_timestamp": str(int(time.time())),
                "oauth_version": "1.0",
            }
        )

        data["oauth_signature"] = self._oauth_client.get_oauth_signature(
            oauthlib.common.Request(url, "POST", body=data)
        )

        return data


def dump_response(response, duration_ms, quiet=False):
    # Print to stderr, so you can the pipe main output to a file easily
    if not quiet:
        print("Response:", response, file=sys.stderr)
        print("Headers:", response.headers, file=sys.stderr)
        print(f"Time: {duration_ms}ms", file=sys.stderr)

    if "json" in response.headers["Content-Type"]:
        print(json.dumps(response.json(), indent=4))
    else:
        print(response.text)

    response.raise_for_status()


def main(args):
    with open(args.spec, encoding="utf-8") as handle:
        config = json.load(handle)

    session = OAuthSession(**config["auth"])

    start = datetime.now()
    response = session.post(**config["request"])
    diff = datetime.now() - start
    duration_ms = diff.seconds * 1000 + diff.microseconds / 1000

    dump_response(response, duration_ms, quiet=args.quiet)


if __name__ == "__main__":
    main(parser.parse_args())
