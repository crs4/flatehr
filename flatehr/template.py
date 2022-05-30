import abc
from typing import Callable, Dict, List, Union

WebTemplate = Dict[str, Union[str, bool, int, float]]


class Template:
    def __init__(self, root: "TemplateNode"):
        self._root = root

    @property
    def root(self) -> "TemplateNode":
        return self._root


class TemplateNode(abc.ABC):
    @property
    @abc.abstractmethod
    def rm_type(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def _id(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def aql_path(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def required(self) -> bool:
        ...

    @property
    @abc.abstractmethod
    def inf_cardinality(self) -> bool:
        ...

    @property
    @abc.abstractmethod
    def annotations(self) -> List[Dict[str, str]]:
        ...

    @property
    @abc.abstractmethod
    def children(self) -> List["TemplateNode"]:
        ...

    @property
    @abc.abstractmethod
    def inputs(self):
        ...

    def __str__(self):
        return f"{self.path}, rm_type={self.rm_type}, cardinality={int(self.required)}:{ '*' if self.inf_cardinality else 1 }"

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

    @abc.abstractmethod
    def get_descendant(self, path: str) -> "TemplateNode":
        ...
