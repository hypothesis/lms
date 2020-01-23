import json
import os
from contextlib import contextmanager
from datetime import datetime, timedelta

from lms.api_client.blackboard_classic import BlackboardClassicClient
from lms.api_client.blackboard_classic.model import BBFile, BBFolder
from lms.api_client.generic_http.client.oauth2_client import (
    OAuth2Settings,
    OAuth2Tokens,
)
from lms.logic.file_tree import File, Folder, TreeBuilder


@contextmanager
def timeit():
    start = datetime.utcnow()
    yield

    diff = datetime.utcnow() - start
    print(diff.microseconds / 1000 + diff.seconds * 1000, "ms")


def save_tokens(token_response):
    print("Saving new tokens...")
    with open("tryit.json", "w") as fh:
        json.dump(token_response, fh, indent=4)


class ItemStream:
    @classmethod
    def list_all_items(cls, api, max_iterations=5, max_seconds=10):
        max_seconds = timedelta(seconds=max_seconds)

        items = []
        offset = 0
        limit = 200  # 200 is the max
        complete = False

        start = datetime.utcnow()

        for _ in range(max_iterations):
            with timeit():
                new_items = api.course(course_id).list_contents(
                    recursive=True,
                    offset=offset,
                    limit=limit,
                    # The fewer fields we ask for the faster this is
                    fields=[
                        "id",
                        "parentId",  # To build tree
                        "contentHandler.id",  # To tell content types apart
                        "contentHandler.file",  # To get the filename / ext
                        "title",  # The main label
                    ],
                )

            items.extend(cls._create_file_tree_items(new_items))
            offset += len(new_items)

            if len(new_items) < limit:
                complete = True
                break

            if (datetime.utcnow() - start) > max_seconds:
                complete = False
                break

        return items, complete

    @classmethod
    def _create_file_tree_items(cls, items):
        for item in items:
            if not isinstance(item, (BBFolder, BBFile)):
                continue

            args = {
                "label": item.title,
                "node_id": item.id,
                "parent_id": item.parent_id,
                "retrieval_id": item.retrieval_id,
            }

            if isinstance(item, BBFile):
                if item.extension != "pdf":
                    continue

                yield File(
                    file_type=item.extension, **args,
                )

            elif isinstance(item, BBFolder):
                yield Folder(**args)


if __name__ == "__main__":
    with open("tryit.json") as fh:
        data = json.load(fh)

    access_token, refresh_token = data["access_token"], data["refresh_token"]

    ws = BlackboardClassicClient(
        settings=OAuth2Settings(
            client_id="e90b19eb-61c5-4a21-95ed-7afefcea273e",
            client_secret=os.environ["CLIENT_SECRET"],
            redirect_uri="https://httpbin.org/get",
        ),
        tokens=OAuth2Tokens(access_token, refresh_token, update_callback=save_tokens),
        host="blackboard.hypothes.is",
    )

    api = ws.api()

    course_id = "07c0a521976e43b68616ad516adaab91"

    with ws.session():
        print("Auth URL:", ws.get_authorize_code_url())
        # print(ws.get_tokens("mR2A233SlqueAFjrGxGQqq0N503d3JNg"))

        # Get all results
        with timeit():
            items, complete = ItemStream.list_all_items(api)

        print(f"Found {len(items)} item(s): {['MORE TO COME', 'COMPLETE'][complete]}")

        tree = TreeBuilder.create(node_stream=items, complete=complete)

        print(json.dumps(tree.as_dict(), indent=4))
