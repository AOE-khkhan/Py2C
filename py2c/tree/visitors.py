"""BaseTreeVisitor and it's concrete subclasses
"""

# -----------------------------------------------------------------------------
# Py2C - A Python to C++ compiler
# Copyright (C) 2014 Pradyun S. Gedam
# -----------------------------------------------------------------------------

import abc
import collections

from py2c.tree import Node, iter_fields


class BaseTreeVisitor(object, metaclass=abc.ABCMeta):
    """ABC of TreeVisitors
    """

    # Serves as a stub when a function needs to return None
    NONE_SENTINEL = object()

    # Arguments allow reuse with similar but different Node systems.
    # (For example, these visitors are compatible with ``ast``)
    def __init__(self, root_class=Node, iter_fields=iter_fields):
        super().__init__()
        self.root_class = root_class
        self.iter_fields = iter_fields

    def visit(self, node):
        """Visits a node.
        """
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def children_visit(self, node):
        raise NotImplementedError()

    @abc.abstractmethod
    def generic_visit(self, node):
        pass


class RecursiveTreeVisitor(BaseTreeVisitor):
    """Visits the base nodes before parent nodes.
    """

    def children_visit(self, node):
        for field, value in self.iter_fields(node):
            value = getattr(node, field, None)

            if isinstance(value, list):
                self._visit_list(value)
            elif isinstance(value, self.root_class):
                self.visit(value)

    def _visit_list(self, original_list):  # coverage: not missing
        for value in original_list:
            if isinstance(value, self.root_class):
                self.visit(value)

    def generic_visit(self, node):
        self.children_visit(node)


class RecursiveTreeTransformer(BaseTreeVisitor):
    """A BaseTreeVisitor that allows modification of Nodes, in-place.

    RecursiveTreeTransformer walks the Tree and uses the return value of the
    visitor methods to replace or remove the Nodes.

    If the return value of the visitor method is:
      1. ``None``: The node will be removed from its location
      2. ``self.NONE_SENTINEL``: The node will be replaced with ``None``
    Otherwise the node is replaced with the return value.
    The return value may be the original node in which case no replacement
    takes place.

    Based off ``ast.NodeTransformer``
    """

    def children_visit(self, node):
        """Visit all children of node.
        """
        for field, old_value in self.iter_fields(node):
            if isinstance(old_value, list):
                self._visit_list(old_value)
            elif isinstance(old_value, self.root_class):
                new_node = self.visit(old_value)
                if new_node is None:
                    delattr(node, field)
                elif new_node is self.NONE_SENTINEL:
                    new_node = None
                setattr(node, field, new_node)

    # Moved out of 'children_visit' for readablity
    def _visit_list(self, original_list):
        new_list = []
        for value in original_list:
            if isinstance(value, self.root_class):
                value = self.visit(value)
                if value is None:
                    continue
                elif value is self.NONE_SENTINEL:
                    value = None
                elif isinstance(value, collections.Iterable):
                    new_list.extend(value)
                    continue
            new_list.append(value)
        original_list[:] = new_list

    def generic_visit(self, node):
        self.children_visit(node)
