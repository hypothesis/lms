import os
from os.path import relpath
from pathlib import Path

import importlib_resources

TEST_ROOT = importlib_resources.files("tests")


def test_for_missing_init_files():
    missing = list(_find_missing())

    message = "You need to add these missing __init__.py file(s):\n\n"
    message += "\n".join(missing)
    message += (
        "\n\n"
        "All directories containing test files need to have __init__.py\n"
        "files, otherwise PyLint doesn't lint them. See:\n\n"
        "https://github.com/hypothesis/lms/issues/1606"
    )
    assert not missing, message


def _find_missing():  # pragma: nocover
    dirs_with_python = set()

    # Find all directories which contain some python and their parents
    for root, dirs, files in os.walk(TEST_ROOT):
        # Ignore `__pycache__` dirs and don't recurse into them
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")

        rel_root = relpath(root, TEST_ROOT)
        if rel_root.startswith("bdd"):
            continue

        # Ignore the cookiecutter's pytest_plugins dir.
        if rel_root == "pytest_plugins":
            continue

        for file in files:
            if file.endswith(".py"):
                dirs_with_python.add(rel_root)
                dirs_with_python.update(Path(rel_root).parents)
                break

    for rel_path in dirs_with_python:
        expected_init = os.path.join(rel_path, "__init__.py")
        abs_path = TEST_ROOT / expected_init

        if not os.path.exists(abs_path):
            yield str(abs_path)
