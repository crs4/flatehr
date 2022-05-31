import abc
from typing import Callable, Dict, List, Union, Optional
from dataclasses import dataclass

WebTemplate = Dict[str, Union[str, bool, int, float]]


class Template:
    def __init__(self, root: "TemplateNode"):
        self._root = root

    @property
    def root(self) -> "TemplateNode":
        return self._root


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
    def ancestors(self) -> List["TemplateNode"]:
        ...

    @property
    @abc.abstractmethod
    def path(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def is_leaf(self) -> bool:
        ...

    @abc.abstractmethod
    def get_descendant(self, path: str) -> "TemplateNode":
        ...
