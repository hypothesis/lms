import os


def test_for_missing_init_files():
    missing = []

    for root, _dirs, files in os.walk("tests"):
        if root.startswith("tests/bdd"):
            continue

        if root.endswith("__pycache__"):  # pragma: no cover
            continue

        if "__init__.py" not in files:  # pragma: no cover
            missing.append(root + "/__init__.py")

    message = "You need to add these missing __init__.py file(s):\n\n"
    message += "\n".join(missing)
    message += (
        "\n\n"
        "All directories containing test files need to have __init__.py\n"
        "files, otherwise PyLint doesn't lint them. See:\n\n"
        "https://github.com/hypothesis/lms/issues/1606"
    )
    assert not missing, message
