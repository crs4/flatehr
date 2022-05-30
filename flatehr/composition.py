import abc
import logging
from typing import Dict, List, Union

from flatehr.data_types import DataValue, Factory, NullFlavour
from flatehr.template import Template

logger = logging.getLogger(__name__)


class Composition(abc.ABC):
    def __init__(
        self,
        root: "CompositionNode",
        metadata: Dict[str, Union[str, int]] = None,
    ):
        self._root = root
        self.metadata = metadata or {}

    @property
    def template(self) -> Template:
        return self.root.template

    @property
    def root(self) -> "CompositionNode":
        return self._root

    def create_node(
        self,
        path: str,
        increment_cardinality: bool = True,
        null_flavour: NullFlavour = None,
        **kwargs,
    ) -> "CompositionNode":
        path = path.replace(f"{self.root.path}", "")
        composition_node = self.root.create_node(
            path, increment_cardinality, null_flavour
        )
        # @fixme it should be on CompositionNode.create_node
        if composition_node.template.is_leaf and not null_flavour:
            value = Factory(composition_node.template).create(**kwargs)
            composition_node.value = value
        return composition_node

    def get(self, path: str) -> "CompositionNode":
        path = path.replace(self.root.name, "").strip("/")
        return self.root.get_descendant(path)

    @abc.abstractmethod
    def set_all(self, name: str, **kwargs) -> "CompositionNode":
        ...

    def as_flat(self):
        flat = {}
        for leaf in self.root.leaves:
            flat.update(leaf.as_flat())
        return flat

    @abc.abstractmethod
    def set_defaults(self):
        ...


class CompositionNode(abc.ABC):
    @property
    @abc.abstractmethod
    def value(self) -> DataValue:
        ...

    @value.setter
    @abc.abstractmethod
    def value(self, value: DataValue):
        ...

    @property
    @abc.abstractmethod
    def template(self):
        ...

    @property
    @abc.abstractmethod
    def path(self):
        ...

    @abc.abstractmethod
    def add_child(
        self,
        name: str,
        value: DataValue = None,
        increment_cardinality: bool = True,
        null_flavour: NullFlavour = None,
    ):
        ...

    @abc.abstractmethod
    def create_node(
        self,
        path: str,
        increment_cardinality: bool = True,
        null_flavour: NullFlavour = None,
        **kwargs,
    ) -> "CompositionNode":
        ...

    @property
    @abc.abstractmethod
    def leaves(self):
        ...

    @abc.abstractmethod
    def get_descendant(self, path: str) -> "CompositionNode":
        ...

    @abc.abstractmethod
    def find_descendants(self, path) -> List["CompositionNode"]:
        ...

    @property
    @abc.abstractmethod
    def parent(self):
        ...

    @property
    @abc.abstractmethod
    def children(self):
        ...

    @abc.abstractmethod
    def set_defaults(self):
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
