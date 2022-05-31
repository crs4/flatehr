import logging
from dataclasses import dataclass
from dataclasses import dataclass

import anytree

logger = logging.getLogger("flatehr")


@dataclass
class Node(anytree.NodeMixin):
    _id: str

    def get_descendant(self, path: str):
        resolver = anytree.Resolver("_id")
        try:
            return resolver.get(self, path)
        except anytree.ChildResolverError as ex:
            raise NodeNotFound(f"node: {self.path}, path {path}") from ex


class NodeNotFound(Exception):
    ...
