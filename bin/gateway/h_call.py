#!/usr/bin/env python
"""
Read Gateway format JSON and make calls to H.

See `docs/gateway/03_testing_tools.md` for more details.
"""

import json
import sys
from argparse import ArgumentParser

from requests import Session

parser = ArgumentParser()
parser.add_argument("--spec", "-s", help="Load call definitions from JSON file")
parser.add_argument(
    "--stdin", "-i", action="store_const", const=True, help="Load from STDIN"
)
parser.add_argument("--call", "-c", help="The end-point to call")
parser.add_argument(
    "--authenticate",
    "-a",
    action="store_const",
    const=True,
    help="Authenticate with a bearer token using `exchange_grant_token` before"
    " making the call",
)


def dump_response(response):
    # Print to stderr, so you can the pipe main output to a file easily
    print("Response:", response, file=sys.stderr)
    print("Headers:", response.headers, file=sys.stderr)

    if "json" in response.headers["Content-Type"]:
        print(json.dumps(response.json(), indent=4))
    else:
        print(response.text)

    response.raise_for_status()


def main(args):
    h_end_points = {}

    # Read the spec file from the usual location if piped in from
    # `oauth_call.py`
    if args.stdin:
        h_end_points.update(json.load(sys.stdin)["api"]["h"])

    # Also read from a JSON file for a manually curated set of calls
    if args.spec:
        with open(args.spec, encoding="utf-8") as handle:
            h_end_points.update(json.load(handle)["api"]["h"])

    if not h_end_points:
        raise ValueError("No config loaded!")

    session = Session()

    if args.authenticate:
        # Perform `exchange_grant_token` with `h` to get access tokens

        response = session.request(**h_end_points["exchange_grant_token"])
        response.raise_for_status()
        access_token = response.json()["access_token"]
        session.headers.update({"Authorization": f"Bearer {access_token}"})

    if args.call:
        # Run a named call
        response = session.request(**h_end_points[args.call])
        dump_response(response)

    else:
        # List all the commands we know about from the loaded specs
        print("Available end-points:")
        for key in h_end_points:
            print(f"\t * {key}")


if __name__ == "__main__":
    main(parser.parse_args())
