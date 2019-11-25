import re
from glob import glob

from behave.parser import parse_file


class FeatureStepGenerator:
    @classmethod
    def from_feature_file(cls, feature_file):
        with open(feature_file) as handle:
            lines = list(handle)

        parsed = parse_file(feature_file)

        start_points = [scenario.line for scenario in parsed.scenarios]
        start_points.append(len(lines) + 1)

        for pos, scenario in enumerate(parsed.scenarios):
            start = scenario.line
            end = start_points[pos + 1] - 1
            body = "".join(lines[start:end]).rstrip()

            yield FeatureStep(scenario, body)

    @classmethod
    def scan_dir(cls, target_dir):
        for feature_file in glob(target_dir + "*.feature"):
            yield from FeatureStepGenerator.from_feature_file(feature_file)

    @classmethod
    def generate(cls, source_dir, target_file):
        python_code = (
            f'"""\nThis code is auto-generated.\n\nFrom {source_dir}.\n"""'
            "\n\nfrom behave import step\n"
        )

        for feature_step in cls.scan_dir(source_dir):
            python_code += "\n\n" + feature_step.function_string()

        with open(target_file, "w") as handle:
            handle.write(python_code)


class FeatureStep:
    NOT_LOWER_CASE = re.compile("[^a-z]+")
    PARAM = re.compile("\\{([a-z_]+)\\}")

    def __init__(self, scenario, body):
        self.scenario = scenario
        self.body = body

    def _function_name(self, name):
        name = name.lower()
        return self.NOT_LOWER_CASE.sub("_", name)

    def function_string(self):
        name = self.scenario.name
        function_name = self._function_name(name)

        extra_parameters = self.PARAM.findall(name)

        signature = ", ".join(["context"] + extra_parameters)
        subs = ", ".join(f"{param}={param}" for param in extra_parameters)

        return f"""@step("{name}")
def {function_name}({signature}):
    # From: {self.scenario.feature.filename}: line {self.scenario.line - 1}
    context.execute_steps(
         \"\"\"
{self.body}
    \"\"\".format(
            {subs}
        )
    )
"""
