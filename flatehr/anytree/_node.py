import logging
from dataclasses import dataclass
from typing import Tuple, cast

import anytree

logger = logging.getLogger("flatehr")


@dataclass
class NodeNotFound(Exception):
    msg: str
    node: "Node"
    child: str


class NodeAlreadyExists(Exception):
    ...


@dataclass
class Node(anytree.NodeMixin):
    _id: str

    def __post_init__(self):
        self._resolver = anytree.Resolver("_id")
        self._walker = anytree.Walker()

    def get(self, path: str) -> "Node":

        try:
            return (
                self._resolver.glob(self, path)
                if "*" in path
                else self._resolver.get(self, path)
            )
        except anytree.ChildResolverError as ex:
            raise NodeNotFound(f"node: {self}, path {path}", ex.node, ex.child) from ex

    def __str__(self) -> str:
        return self.separator.join([cast(Node, n)._id for n in super().path])

    def walk_to(self, dest: "Node") -> Tuple["Node", ...]:
        upwards, common, downwards = self._walker.walk(self, dest)
        return (upwards + (common,) + downwards)[1:]

    def find(self, _id: str):
        return anytree.search.findall(self, filter_=lambda n: n._id == _id)
