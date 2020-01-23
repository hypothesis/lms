from enum import Enum


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
        self.complete = True

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


class Traversal(Enum):
    BFS = "breadth_first_search"
    DFS = "depth_first_search"


class TreeBuilder:
    # TODO! - Loads of this could be more efficient by rendering a guaranteed
    # parent first flat ordering (basically DFS or BFS). This would allow many
    # of the recursive functions to become linear scans.

    @classmethod
    def create(
        cls,
        node_stream,
        complete=True,
        traversal=Traversal.DFS,
        remove_empty_folders=True,
        remove_leading_folders=True,
    ):

        tree = cls.build_tree(node_stream)

        if not complete:
            cls.mark_complete(tree, traversal)

        if remove_empty_folders:
            cls.remove_empty_folders(tree)

        if remove_leading_folders:
            tree = cls.remove_leading_folders(tree)

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
    def mark_complete(cls, tree, traversal=Traversal.DFS):
        """
        Mark the folder nodes as either complete or not depending on traversal.

        When a large tree of files and folders is traversed and the traversal
        stops before all files are folders are reached, some folders will be
        incomplete. This discovers and marks these folders.

        :param tree: Tree to mark
        :param traversal: The traversal order the nodes were found in
        """

        # There's only one traversal method available, but we should force the
        # caller to specify it to make them think about whether their tree was
        # traversed in DFS or BFS or something else (random?)
        if traversal == Traversal.DFS:
            cls._mark_rhs_incomplete(tree)

        else:
            # To implement BFS we should find and mark the last folder we
            # found as not complete.
            raise NotImplementedError(
                "I don't know how to tell if your tree is finished"
            )

    @classmethod
    def remove_empty_folders(cls, node):
        """Remove empty folders or folders only containing empty folders."""
        if not isinstance(node, Folder):
            return

        for child in list(node.children):
            cls.remove_empty_folders(child)

        if not node.children:
            node.parent.remove_child(node)

    @classmethod
    def remove_leading_folders(cls, root):
        """Remove root folders containing only a single folder."""

        while isinstance(root, Folder) and len(root.children) == 1:
            root = root.children[0]
            root.parent = None
            root.parent_id = None

        return root

    @classmethod
    def _mark_rhs_incomplete(cls, node):
        # In a DFS traversal the last folder, and all of it's parents are
        # potentially incomplete. We therefore should recurse along the RHS
        # Of the tree marking each folder as incomplete

        if not isinstance(node, Folder):
            return

        node.complete = False

        if node.children:
            cls._mark_rhs_incomplete(node.children[-1])
