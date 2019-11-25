"""Creates step definitions from feature files."""

import re
from glob import glob

from behave.parser import parse_file

__ALL__ = ["Injector"]


class FeatureStep:
    """A step created from a feature file."""

    def __init__(self, scenario, params, body):
        self.scenario = scenario
        self.params = params
        self.body = body


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

    @classmethod
    def render_steps(cls, feature_steps, source_dir):
        python_code = (
            f'"""\nThis code is auto-generated.\n\nFrom {source_dir}.\n"""'
            "\n\nfrom behave import step\n"
        )

        for feature_step in feature_steps:
            python_code += "\n\n" + cls.render_step(feature_step)

        return python_code

    @classmethod
    def render_step(cls, step):
        signature = ", ".join(["context"] + step.params)
        subs = ", ".join(f"{param}={param}" for param in step.params)
        function_name = cls._function_name(step.name)

        return f"""@step("{step.name}")
        def {function_name}({signature}):
            # From: {step.scenario.feature.filename}: line {step.scenario.line - 1}
            context.execute_steps(
                 \"\"\"
        {step.body}
            \"\"\".format(
                    {subs}
                )
            )
        """

    @classmethod
    def _function_name(cls, name):
        name = name.lower()
        return cls.NOT_LOWER_CASE.sub("_", name)
