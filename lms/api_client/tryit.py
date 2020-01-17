import json
import os
from contextlib import contextmanager
from datetime import datetime
from pprint import pprint

from lms.api_client.blackboard_classic import BlackboardClassicClient
from lms.api_client.blackboard_classic.model import File, Folder
from lms.api_client.generic_http.oauth2.manager import OAuth2Manager


@contextmanager
def timeit():
    start = datetime.utcnow()
    yield

    diff = datetime.utcnow() - start
    print(diff.microseconds / 1000 + diff.seconds * 1000, "ms")


def load_tokens():
    with open("tryit.json") as fh:
        data = json.load(fh)

        return data["access_token"], data["refresh_token"]


def save_tokens(token_response):
    print("Saving new tokens...")
    with open("tryit.json", "w") as fh:
        json.dump(token_response, fh, indent=4)


if __name__ == "__main__":
    access_token, refresh_token = load_tokens()

    ws = BlackboardClassicClient(host="blackboard.hypothes.is")
    auth = OAuth2Manager(
        ws,
        client_id="e90b19eb-61c5-4a21-95ed-7afefcea273e",
        client_secret=os.environ["CLIENT_SECRET"],
        redirect_uri="https://httpbin.org/get",
        token_callback=save_tokens,
    ).set_tokens(access_token=access_token, refresh_token=refresh_token)

    api = ws.api()

    course_id = "07c0a521976e43b68616ad516adaab91"

    course = api.course(course_id)
    print(course.get_retrieval_id())
    print(course.parse_retreival_id(course.get_retrieval_id()))

    from urllib.parse import urlencode

    wat = urlencode(api.course(course_id).content("_258_1").get_arguments())
    print(wat)

    with auth.session():
        print("Auth URL:", auth.get_authorize_code_url())
        # print(auth.get_tokens("ifCaJ4oglLIDOnqT7Ie69QfSNEqsZ0zL"))

        # pprint(api.course(course_id).content("root").get())

        with timeit():
            items = []
            offset = 0
            while True:
                with timeit():
                    new_items = api.course(course_id).list_contents(
                        recursive=True,
                        fields=[
                            "title",
                            "hasChildren",
                            "id",
                            "parentId",
                            "contentHandler.id",
                            "createdDate",
                        ],
                        offset=offset,
                        limit=1,
                    )

                items.extend(new_items)
                offset += len(new_items)

                break
                if len(new_items) < 200:
                    break

        print("ALL THINGS", len(items))
        # items = [item for item in items if isinstance(item, (Folder, File))]
        print("FILE THINGS", len(items))

        tree_items = {None: {"children": []}}
        for item in items:
            item["children"] = []
            tree_items[item["id"]] = item

            tree_items[item.get("parentId")]["children"].append(item)

        # pprint(tree_items[None])

        def dump_tree(items, indent=0):
            for item in items:
                if isinstance(item, Folder):
                    print(("     " * indent) + f">{indent} {item.title}/")
                    dump_tree(item["children"], indent + 1)
                else:
                    print(("     " * indent) + f">{indent} * {item.title}")

        tree = tree_items[None]["children"]

        dump_tree(tree)

        exit()

        while stack:
            item = stack.pop()

            if isinstance(item, Folder) and item.has_children:
                print(f"Folder: {item.title}/ #{item.id}")
                with timeit():
                    stack.extend(item.children())

            elif isinstance(item, File):
                print(f"{item.filename} #{item.id}, Retrieval id {item.retrieval_id}")

                # with timeit():
                #     attachment = retrieve_attachment(api, item.retrieval_id)
                #
                # with timeit():
                #     print(attachment.download_url)

                # print("ATT_ID", attachment.id)
