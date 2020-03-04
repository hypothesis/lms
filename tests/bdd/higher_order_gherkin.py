"""Creates step definitions from feature files."""

import os
import re
from glob import glob

from behave.parser import parse_file
from pkg_resources import resource_filename

__ALL__ = ["Injector"]


class FeatureStep:
    """A step created from a feature file."""

    def __init__(self, scenario, params, body):
        self.scenario = scenario
        self.params = params
        self.body = body

    @property
    def name(self):
        return self.scenario.name

    @property
    def filename(self):
        return self.scenario.feature.filename

    @property
    def line_no(self):
        return self.scenario.line


class Injector:
    """Inject feature generated steps into your code base."""

    @classmethod
    def create_step_file(cls, source_dir, target_file):
        python_code = Renderer.render_steps(
            cls._scan_dir(source_dir), source_dir=source_dir
        )

        with open(target_file, "w") as handle:
            handle.write(python_code)

    @classmethod
    def _scan_dir(cls, target_dir):
        for feature_file in glob(target_dir + "*.feature"):
            yield from Parser.parse_feature_file(feature_file)


class Parser:
    """Parse feature files into steps."""

    PARAM = re.compile("{([a-z_]+)}")

    @classmethod
    def parse_feature_file(cls, feature_file):
        with open(feature_file) as handle:
            lines = list(handle)

        parsed = parse_file(feature_file)

        start_points = [scenario.line for scenario in parsed.scenarios]
        start_points.append(len(lines) + 1)

        for pos, scenario in enumerate(parsed.scenarios):
            start = scenario.line
            end = start_points[pos + 1] - 1
            body = "".join(lines[start:end]).rstrip()

            yield FeatureStep(
                scenario=scenario,
                params=cls._parse_function_name(scenario.name),
                body=body,
            )

    @classmethod
    def _parse_function_name(cls, name):
        return cls.PARAM.findall(name)


class Renderer:
    """Render steps into Python code."""

    NOT_LOWER_CASE = re.compile("[^a-z]+")
    FORMAT_REMOVER = re.compile(r"\.format\(\s+\)", re.MULTILINE)

    @classmethod
    def render_steps(cls, feature_steps, source_dir):
        # Make the source_dir relative to the project to prevent us from adding
        # local file layout details
        source_dir = os.path.relpath(source_dir, resource_filename("tests", "../"))

        python_code = (
            f'"""\nAuto-generated.\n\nFrom {source_dir}/.\n"""'
            "\n\nfrom behave import step  # pylint:disable=no-name-in-module\n"
        )

        for feature_step in sorted(feature_steps, key=lambda step: step.name):
            python_code += "\n\n" + cls.render_step(feature_step)

        return python_code

    @classmethod
    def render_step(cls, step):
        signature = ", ".join(["context"] + step.params)
        subs = ", ".join(f"{param}={param}" for param in step.params)
        function_name = cls._function_name(step.name)

        python_code = f"""@step("{step.name}")
def {function_name}({signature}):
    # From: {step.filename}: line {step.line_no - 1}
    context.execute_steps(
        \"\"\"
{step.body}
    \"\"\".format(
            {subs}
        )
    )
"""
        python_code = cls.FORMAT_REMOVER.sub("", python_code)

        return python_code

    @classmethod
    def _function_name(cls, name):
        name = name.lower()
        return cls.NOT_LOWER_CASE.sub("_", name.strip()).strip("_")
