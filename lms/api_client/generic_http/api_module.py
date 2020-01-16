from collections import deque


class APIModule:
    def __init__(self, ws, parent=None, path_part=""):
        self.ws = ws
        self.path_part = path_part
        self.parent = parent

    def ancestry(self):
        ancestors = deque([self])

        parent = self.parent
        while parent is not None:
            ancestors.appendleft(parent)
            parent = parent.parent

        return ancestors

    def path(self, suffix=None):
        path = "".join(module.path_part for module in self.ancestry())

        if suffix:
            path += "/" + suffix.lstrip("/")

        return path

    def extend(self, child_class, *args, **kwargs):
        return child_class(self.ws, self, *args, **kwargs)

    def call(self, method, path, query=None, headers=None):
        return self.ws.call(method, self.path(path), query, headers)

    def oauth2_call(self, method, path, query=None, headers=None):
        return self.ws.oauth2_call(method, self.path(path), query, headers)
