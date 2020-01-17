from collections import deque
from urllib.parse import parse_qsl, urlencode


class APIModule:
    def __init__(self, ws, parent=None, template_part="", arguments=None):
        self.ws = ws
        self.template_part = template_part
        self.arguments = arguments or {}
        self.parent = parent

    def extend(self, child_class, *args, **kwargs):
        return child_class(self.ws, self, *args, **kwargs)

    def call(self, method, path, query=None, headers=None, **options):
        return self.ws.call(method, self._path(path), query, headers, **options)

    def get_retrieval_id(self):
        return urlencode(self._get_arguments())

    @staticmethod
    def parse_retreival_id(retrieval_id):
        return dict(parse_qsl(retrieval_id))

    def _ancestry(self):
        ancestors = deque([self])

        parent = self.parent
        while parent is not None:
            ancestors.appendleft(parent)
            parent = parent.parent

        return ancestors

    def _get_arguments(self):
        arguments = {}
        for ancestor in self._ancestry():
            arguments.update(ancestor.arguments)

        return arguments

    def _template(self, suffix=None):
        template = "".join(module.template_part for module in self._ancestry())

        if suffix:
            template += "/" + suffix.lstrip("/")

        return template

    def _path(self, suffix=None):
        template = self._template(suffix)
        args = self._get_arguments()

        return template.format(**args)
