import abc
import logging
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Union


from flatehr.rm import NullFlavour, RMObject
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
    def root(self) -> "CompositionNode":
        return self._root

    @property
    def template(self) -> Template:
        return self._template

    def __getitem__(
        self, path: str
    ) -> Union["CompositionNode", List["CompositionNode"]]:
        path = path.replace(self._root._id, "", 1).strip("/")
        return self._root[path]

    def __setitem__(self, path, value: Union[RMObject, "CompositionNode"]):
        path = self._remove_root_path(path)
        self._root[path] = value

    def add(self, path: str) -> str:
        path = self._remove_root_path(path)
        return self._root.add(path)

    def _remove_root_path(self, path: str) -> str:
        return re.sub(f"(\/?{self._root._id}/)", "", path)

    def as_flat(self):
        flat = {}
        for leaf in self._root.leaves:
            if leaf.template.is_leaf:
                flat.update(leaf.as_flat())
        return flat

    def set_defaults(self):
        for path in self.get_required_leaves():
            try:
                self[path] = self.template[path].default
            except InvalidDefault as ex:
                logger.error(ex)

    def get_required_leaves(self, _id: Optional[str] = None) -> List[str]:
        return [
            os.path.join(self._root._id, path)
            for path in self._root.get_required_leaves(_id)
        ]


@dataclass
class CompositionNode(abc.ABC):
    template: TemplateNode
    value: Optional[RMObject] = None
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
    def __setitem__(self, path, value: Union[RMObject, "CompositionNode"]):
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

    @abc.abstractmethod
    def get_required_leaves(self, _id: Optional[str] = None) -> List[str]:
        ...


class NotaLeaf(Exception):
    ...


class IncompatibleDataType(Exception):
    ...


class InvalidDefault(Exception):
    ...


#  def build(composition: Composition, source: Source, converter: Converter):
#      def populate_composition(composition, path, value):
#          if value:
#              composition[path] = value
#          else:
#              composition.add(path)
#
#      list(
#          source.iter()
#          | map(lambda m: (m.template_node, converter.convert(m.template_node, m.value)))
#          | map(lambda el: populate_composition(composition, *el))
#      )
