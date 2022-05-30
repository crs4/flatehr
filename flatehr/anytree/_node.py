import logging
from dataclasses import dataclass
from typing import Any, List

import anytree

logger = logging.getLogger("flatehr")


class Node:
    def __init__(self, node: anytree.Node):
        assert type(node) == anytree.Node
        self._node = node

    def __str__(self):
        return str(self._node)

    def _set_value(self, value):
        self._node.value = value

    def _get_value(self):
        return self._node.value

    value = property(_get_value, _set_value)

    @property
    def is_leaf(self) -> bool:
        return self._node.is_leaf

    @property
    def separator(self):
        return self._node.separator

    @property
    def name(self):
        return self._node.name

    @property
    def leaves(self):
        for leaf in self._node.leaves:
            yield type(self)(leaf)

    def walk_to(self, node: "Node") -> List["Node"]:
        walker = anytree.walker.Walker()
        return [type(self)(node_) for node_ in walker.walk(self._node, node._node)[2]]

    @property
    def path(self):
        return (
            self._node.separator
            + self._node.separator.join([n.name for n in self._node.path])
            + self._node.separator
        )

    @property
    def children(self) -> List["Node"]:
        return [Node(child) for child in self._node.children]

    def get_descendant(self, path: str) -> "Node":
        resolver = anytree.Resolver("name")
        #  return type(self)(resolver.get(self._node, path))
        try:
            return type(self)(resolver.get(self._node, path))
        except anytree.ChildResolverError as ex:
            raise NodeNotFound(f"node: {self.path}, path {path}")

    @property
    def parent(self):
        parent = self._node.parent
        return type(self)(parent)

    def render(self) -> str:
        return anytree.RenderTree(self._node)

    @property
    def attrs(self) -> "NodeAttrs":
        return NodeAttrs(self._node)

    @property
    def ancestors(self) -> List["Node"]:
        return self.walk_to(anytree.Node("/"))


@dataclass
class NodeAttrs:
    node: anytree.Node

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self.node, key)
        except AttributeError as ex:
            raise KeyError() from ex

    def __setitem__(self, key: str, value: Any):
        setattr(key, value)


class NodeNotFound(Exception):
    ...
