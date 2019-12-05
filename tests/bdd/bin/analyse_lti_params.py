"""
Make a file of the most common params for each section listing differences.

This script will read all the ini files from the LTI specification tool and
attempt to work out an 'most_common' baseline file to use for the section and
generate a file called ``most_common.ini`` for it.

It will then generate differences and make suggestions for configuring each
test in that section and print them out in:

 * A gherkin style: for direct inclusion in scenarios
 * An ini style: for creating smaller fixture files

Nothing will happen with this output: it's up to you to use it or not as you
see fit.

This is only used as a helper when writing the tests and doesn't form part of
the final system.
"""
import os.path
from collections import Counter, defaultdict
from glob import glob

from tests.bdd.steps.the_fixture import TheFixture


def list_ini_files(fixture):
    for file_name in sorted(glob(fixture.get_path("src/*.*.ini"))):
        yield os.path.join("src", os.path.basename(file_name))


def load_ini(fixture, filename):
    values = fixture.load_ini(filename, "dummy")

    bad_keys = {
        "oauth_consumer_key",
        "oauth_nonce",
        "oauth_signature",
        "oauth_timestamp",
        "oauth_consumer_secret",
    }

    final = {}
    for key, value in values.items():
        if key in bad_keys:
            continue

        final[key] = value

    return final


def generate_most_common_values(fixture, threshold):
    # Create a dict which will automatically create a Counter object if you
    # refer to a key. We will use this to store the param as the key, then
    # store each different value we see along with how many times we have seen
    # it for each param.
    value_counts = defaultdict(Counter)
    files = 0

    for filename in list_ini_files(fixture):
        files += 1

        values = load_ini(fixture, filename)

        for key, value in values.items():
            value_counts[key].update({value: 1})

    cutoff = files * threshold

    for key, counts in value_counts.items():
        # Pick out only the most common value for this param
        for value, count in counts.most_common(1):
            if count < cutoff:
                print(
                    f"Skipping {key}={value} as it has too few occurences: {count}/{files}"
                )
            else:
                yield key, value


def write_ini(filename, values):
    with open(filename, "w") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def dump_ini(values):
    for key, value in values.items():
        print(f"{key}={value}")


def write_most_common_file(fixture, threshold):
    most_common = dict(generate_most_common_values(fixture, threshold))
    filename = fixture.get_path("most_common.ini")
    write_ini(filename, most_common)

    return most_common


def generate_diff(fixture, most_common, filename):
    values = load_ini(fixture, filename)

    most_common_keys = set(most_common.keys())
    value_keys = set(values.keys())

    for missing_key in most_common_keys - value_keys:
        yield missing_key, "*MISSING*"

    for key, value in values.items():
        if key not in most_common or most_common[key] != value:
            yield key, value


def write_table(data):
    max_key = max(len(key) for key in data.keys())
    max_value = max(len(value) for value in data.values())

    print("\tGiven I update the fixture 'params' with")
    print(f"      | {'Key':<{max_key}} | {'Value':<{max_value}} |")
    for key, value in sorted(data.items()):
        print(f"      | {key:<{max_key}} | {value:<{max_value}} |")


def generate_param_values(fixture, most_common):
    for filename in list_ini_files(fixture):
        print(f"\n# For {filename}\n")

        diff = dict(generate_diff(fixture, most_common, filename))
        if diff:
            if len(diff) == 1:
                key = list(diff.keys())[0]
                value = list(diff.values())[0]
                print(f"\tGiven I set the fixture 'params' key '{key}' to '{value}'")
            else:
                write_table(diff)
                print()
                dump_ini(diff)
        else:
            print("No detectable difference! - Maybe OAuth params?")


if __name__ == "__main__":
    # These values for thresholds were arrived at by experimentation. Some of
    # the sections are more similar than others. Basically I played with the
    # numbers until I started seeing nice results.

    for section, threshold in {1: 0.5, 2: 0.75, 3: 0.75, 4: 0.5}.items():
        fixture = TheFixture()
        fixture.set_base_dir(f"/lti_certification_1_1/section_{section}")

        print(f"\nSection {section} --------------------------------------\n")
        print("\nGenerating most_common fixture...\n")
        most_common = write_most_common_file(fixture, threshold)

        print("\nDifferences from the most_common...\n")
        generate_param_values(fixture, most_common)
