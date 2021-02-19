"""
Quick script to reformat requirements.txt formatted by
pip-tools<5.0.5 to the format used by newer versions.

This is required as dependabot uses the newer version
but our local enviroments can't upgrade
due to venv-update being tied to older version of pip.

Every dependency update involves a full file
rewrite which is impossible to review without this script.

tox 4.0 could potentially deprecate the need for venv-update

Details about the issue in tox:
    https://github.com/tox-dev/tox/issues/149

and progress on the 4.0 release:
    https://tox.readthedocs.io/en/rewrite/changelog.html
"""
import re
import sys

requirements_path = sys.argv[1]

formatted_lines = []

MULTI_DEP = re.compile(r".* # via .*,.*$")
COMMENT = re.compile(r"^#")


def _remove_trailing(string):
    return re.sub(r"[ ]+$", "", string, flags=re.MULTILINE)


with open(requirements_path, "r") as f:
    for line in f:
        # Comments in the original file
        if COMMENT.match(line):
            formatted_lines.append(line)
            continue

        if not MULTI_DEP.match(line):
            # Requirements with only one entry in "via" are kept in the same line:
            # package==XX # via other_package
            #   becomes
            # package==XX
            #   # via other_package
            formatted = line.replace("# via", "\n    # via")
            formatted_lines.append(_remove_trailing(formatted))
            continue

        # For multiple entries in `# via` gets it's own line
        # package==XX # via other_package, and_another
        #   becomes
        # package==XX
        #   # via
        #   #   other_package
        #   #   and_another
        formatted = line.replace("# via", "\n    # via \n    #  ")
        formatted = formatted.replace(", ", "\n    #   ")
        formatted_lines.append(_remove_trailing(formatted))


with open(requirements_path, "w") as f:
    f.write("".join(formatted_lines))
