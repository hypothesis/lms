from collections import deque


class APIModule:
    def __init__(self, ws, parent=None, template_part="", arguments=None):
        self.ws = ws
        self.template_part = template_part
        self.arguments = arguments or {}
        self.parent = parent

    def ancestry(self):
        ancestors = deque([self])

        parent = self.parent
        while parent is not None:
            ancestors.appendleft(parent)
            parent = parent.parent

        return ancestors

    def get_arguments(self):
        arguments = {}
        for ancestor in self.ancestry():
            arguments.update(ancestor.arguments)

        return arguments

    def template(self, suffix=None):
        template = "".join(module.template_part for module in self.ancestry())

        if suffix:
            template += "/" + suffix.lstrip("/")

        return template

    def path(self, suffix=None):
        template = self.template(suffix)
        args = self.get_arguments()

        return template.format(**args)

    def extend(self, child_class, *args, **kwargs):
        return child_class(self.ws, self, *args, **kwargs)

    def call(self, method, path, query=None, headers=None, **options):
        return self.ws.call(method, self.path(path), query, headers, **options)
