class Node:
    def __init__(self, label, node_id, retrieval_id, parent_id=None, parent=None):
        self.id = node_id
        self.parent_id = parent_id
        self.parent = parent

        self.retrieval_id = retrieval_id
        self.label = label

    def as_dict(self):
        return {
            "id": self.retrieval_id,
            "label": self.label,
            "type": self.__class__.__name__,
        }


class File(Node):
    def __init__(self, label, file_type, node_id, retrieval_id, parent_id=None):
        super().__init__(label, node_id, retrieval_id, parent_id)

        self.file_type = file_type

    def as_dict(self):
        data = super().as_dict()
        data["fileType"] = self.file_type

        return data


class Folder(Node):
    def __init__(self, label, node_id, retrieval_id, parent_id=None):
        super().__init__(label, node_id, retrieval_id, parent_id)

        self.children = []
        self.complete = False

    def add_child(self, node):
        self.children.append(node)
        node.parent = self

    def remove_child(self, node):
        self.children.remove(node)
        node.parent = None

    def as_dict(self):
        data = super().as_dict()
        data["children"] = [child.as_dict() for child in self.children]

        if not self.complete:
            data["complete"] = False

        return data


class TreeBuilder:
    # TODO! - Loads of this could be more efficient by rendering a guaranteed
    # parent first flat ordering (basically DFS or BFS). This would allow many
    # of the recursive functions to become linear scans.

    @classmethod
    def create(
        cls,
        node_stream,
        complete=True,
        ordering="dfs",
        prune_empty=True,
        prune_leading_singletons=True,
    ):

        tree = cls.build_tree(node_stream)
        cls.mark_complete(tree, complete, ordering)
        if prune_empty:
            cls.prune_empty(tree)

        if prune_leading_singletons:
            tree = cls.prune_leading_singletons(tree)

        return tree

    @classmethod
    def build_tree(cls, node_stream):
        root = Folder("Root", node_id=None, retrieval_id=None)
        nodes_by_id = {None: root}

        for node in node_stream:
            if not isinstance(node, (File, Folder)):
                raise TypeError("Expected a TreeBuilder File or Folder")

            nodes_by_id[node.id] = node

        for node in node_stream:
            nodes_by_id[node.parent_id].add_child(node)

        return root

    @classmethod
    def mark_complete(cls, tree, complete=True, ordering="dfs"):
        if complete:
            cls._mark_all_complete(tree)
        elif ordering == "dfs":
            cls._mark_rhs_incomplete(tree)
        elif ordering == "bfs":
            cls._mark_all_complete(tree)
            cls._mark_last_incomplete(tree)
        else:
            raise NotImplementedError(
                "I don't know how to tell if your tree is finished"
            )

    @classmethod
    def prune_empty(cls, node):
        if not isinstance(node, Folder):
            return

        for child in list(node.children):
            cls.prune_empty(child)

        if not node.children:
            node.parent.remove_child(node)

    @classmethod
    def prune_leading_singletons(cls, root):
        while isinstance(root, Folder) and len(root.children) == 1:
            root = root.children[0]
            root.parent = None
            root.parent_id = None

        return root

    @classmethod
    def _mark_all_complete(cls, node):
        if not isinstance(node, Folder):
            return

        node.complete = True
        for child in node.children:
            cls._mark_all_complete(child)

    @classmethod
    def _mark_rhs_incomplete(cls, node):
        if not isinstance(node, Folder) or not node.children:
            return

        node.complete = False

        cls._mark_rhs_incomplete(node.children[-1])

        for child in node.children[:-1]:
            cls._mark_all_complete(child)

    @classmethod
    def _mark_last_incomplete(cls, node):
        if not isinstance(node, Folder):
            raise TypeError("This must be called on a folder")

        # Find last folder
        for child in reversed(node.children):
            if isinstance(child, Folder):
                return cls._mark_last_incomplete(child)

        # We are the last one!
        node.complete = False
