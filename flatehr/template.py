import abc
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

from pipe import chain, map

WebTemplate = Dict[str, Union[str, bool, int, float]]


class Template:
    def __init__(self, root: "TemplateNode"):
        self._root = root

    @property
    def root(self) -> "TemplateNode":
        return self._root

    def __getitem__(self, path: str) -> "TemplateNode":
        path = path.replace(self.root._id, "", 1).lstrip("/")
        return self.root.get(path)


@dataclass
class TemplateNode(abc.ABC):
    _id: str
    rm_type: str
    aql_path: str
    required: bool
    inf_cardinality: bool
    annotations: Optional[List[Dict[str, str]]] = None
    inputs: Optional[Dict[str, str]] = None

    @property
    @abc.abstractmethod
    def children(self) -> List["TemplateNode"]:
        ...

    @property
    @abc.abstractmethod
    def parent(self) -> "TemplateNode":
        ...

    @property
    @abc.abstractmethod
    def path(self) -> Tuple["TemplateNode", ...]:
        ...

    @property
    @abc.abstractmethod
    def ancestors(self) -> Tuple["TemplateNode", ...]:
        ...

    @property
    @abc.abstractmethod
    def is_leaf(self) -> bool:
        ...

    @abc.abstractmethod
    def walk_to(self, dest: "TemplateNode") -> "TemplateNode":
        ...

    @abc.abstractmethod
    def get(self, path) -> "TemplateNode":
        ...


def remove_cardinality(path: str) -> str:
    return re.sub(r"(:[0-9]+)", "", path)


def to_string(
    node: TemplateNode,
    relative_to: Optional[TemplateNode] = None,
    wildcard: bool = False,
) -> str:
    nodes = (
        node.ancestors + (node,) if relative_to is None else relative_to.walk_to(node)
    )
    path = "/".join(
        nodes | map(lambda n: f"{n._id}:*" if n.inf_cardinality and wildcard else n._id)
    )
    return path