import abc
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from flatehr.data_types import DATA_VALUE, NullFlavour
from flatehr.template import Template, TemplateNode

logger = logging.getLogger(__name__)


class Composition:
    def __init__(
        self,
        template: Template,
        root: "CompositionNode",
        metadata: Optional[Dict[str, Union[str, int]]] = None,
    ):
        self._template = template
        self._root = root
        self.metadata = metadata or {}

    @property
    def template(self) -> Template:
        return self._template

    def __getitem__(
        self, path: str
    ) -> Union["CompositionNode", List["CompositionNode"]]:
        path = path.replace(self._root._id, "", 1).strip("/")
        return self._root[path]

    def __setitem__(self, path, value: Union[DATA_VALUE, "CompositionNode"]):
        path = self._remove_root_path(path)
        self._root[path] = value

    #  def list(self, path: str)->"CompositionNode":
    #      return self._root.
    #
    def add(self, path: str) -> str:
        path = self._remove_root_path(path)
        return self._root.add(path)

    def _remove_root_path(self, path: str) -> str:
        return path.replace(self._root._id, "", 1).strip("/")

    #  def create_node(
    #      self,
    #      path: str,
    #      increment_cardinality: bool = True,
    #      null_flavour: Optional[NullFlavour] = None,
    #      **kwargs,
    #  ) -> "CompositionNode":
    #      path = path.replace(f"{self.root.path}", "")
    #      composition_node = self.root.create_node(
    #          path, increment_cardinality, null_flavour
    #      )
    #      # @fixme it should be on CompositionNode.create_node
    #      if composition_node.template.is_leaf and not null_flavour:
    #          value = Factory(composition_node.template).create(**kwargs)
    #          composition_node.value = value
    #      return composition_node
    #
    #  def get(self, path: str) -> "CompositionNode":
    #      path = path.replace(self.root._id, "").strip("/")
    #      return self.root.get_descendant(path)
    #
    # @FIXME: restore method
    #  @abc.abstractmethod
    #  def set_all(self, name: str, **kwargs) -> "CompositionNode":
    #      ...

    def as_flat(self):
        flat = {}
        for leaf in self._root.leaves:
            if leaf.template.is_leaf:
                flat.update(leaf.as_flat())
        return flat

    # @fixme
    #  @abc.abstractmethod
    #  def set_defaults(self):
    #      ...


@dataclass
class CompositionNode(abc.ABC):
    template: TemplateNode
    value: Optional[DATA_VALUE] = None
    null_flavour: Optional[NullFlavour] = None

    def __post_init__(self):
        self._id = self.template._id

    @property
    @abc.abstractmethod
    def path(self) -> str:
        ...

    @abc.abstractmethod
    def __getitem__(self, path) -> Union["CompositionNode", List["CompositionNode"]]:
        ...

    @abc.abstractmethod
    def __setitem__(self, path, value: Union[DATA_VALUE, "CompositionNode"]):
        ...

    @property
    @abc.abstractmethod
    def leaves(self) -> List["CompositionNode"]:
        ...

    @property
    @abc.abstractmethod
    def parent(self):
        ...

    @parent.setter
    @abc.abstractmethod
    def parent(self, value: "CompositionNode"):
        ...

    @property
    @abc.abstractmethod
    def children(self):
        ...

    @abc.abstractmethod
    def set_defaults(self):
        ...

    @abc.abstractmethod
    def add(self, path: str) -> str:
        ...

    def as_flat(self):
        flat = {}
        if self.template.is_leaf:

            value = self.value
            if value is None:
                raise AttributeError(f"value and null_flavour of {self} not set")

            flat.update(value.to_flat(f"{self.path.strip('/')}"))
        else:
            for leaf in self.leaves:
                flat.update(leaf.as_flat())
        return flat


class NotaLeaf(Exception):
    ...


class IncompatibleDataType(Exception):
    ...
