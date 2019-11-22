import os.path
from collections import Counter, defaultdict
from glob import glob

from tests.bdd.steps.the_fixture import TheFixture


def list_ini_files(fixture):
    for file_name in sorted(glob(fixture.get_path("*.*.ini"))):
        yield os.path.basename(file_name)


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


def generate_most_common_values(fixture):
    value_counts = defaultdict(Counter)
    files = 0

    for filename in list_ini_files(fixture):
        files += 1

        values = load_ini(fixture, filename)

        for key, value in values.items():
            value_counts[key].update({value: 1})

    CUTOFF = files // 2

    for key, counts in value_counts.items():
        for value, count in counts.most_common(1):
            if count < CUTOFF:
                print(f"Skipping {key}={value} as it has too few occurences: {count}")
            else:
                yield key, value


def write_ini(filename, values):
    with open(filename, "w") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def write_average_file(fixture):
    average = dict(generate_most_common_values(fixture))
    filename = fixture.get_path("average.ini")
    write_ini(filename, average)

    return average


def generate_diff(fixture, average, filename):
    values = load_ini(fixture, filename)

    average_keys = set(average.keys())
    value_keys = set(values.keys())

    for missing_key in average_keys - value_keys:
        yield missing_key, "*MISSING*"

    for key, value in values.items():
        if key not in average or average[key] != value:
            yield key, value


def write_table(data):
    max_key = max(len(key) for key in data.keys())
    max_value = max(len(value) for value in data.values())

    print("\tGiven I update the fixture 'params' with")
    print(f"      | {'Key':<{max_key}} | {'Value':<{max_value}} |")
    for key, value in sorted(data.items()):
        print(f"      | {key:<{max_key}} | {value:<{max_value}} |")


def generate_param_values(fixture):
    for filename in list_ini_files(fixture):
        print(f"\n# For {filename}\n")

        diff = dict(generate_diff(fixture, average, filename))
        if diff:
            if len(diff) == 1:
                key = list(diff.keys())[0]
                value = list(diff.values())[0]
                print(f"\tGiven I set the fixture 'params' key '{key}' to '{value}'")
            else:
                write_table(diff)
        else:
            print("No detectable difference! - Maybe OAuth params?")


if __name__ == "__main__":
    section = 2

    fixture = TheFixture()
    fixture.set_base_dir(f"/lti_certification_1_1/section_{section}")
    average = write_average_file(fixture)
    generate_param_values(fixture)
