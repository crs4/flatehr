import abc
import logging
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple, TypeVar, Union, cast

from pipe import map


logger = logging.getLogger(__name__)
WebTemplate = Dict[str, Union[str, bool, int, float]]
TemplatePath = str

TNode = TypeVar("TNode", bound="_Node")


@dataclass
class NullFlavour(Dict):
    # place_holder is a workaround for ehrbase expecting value even in case of NullFlavour
    # (at least for some data types)
    value: str
    code: str
    terminology: str
    place_holder: Optional[str] = None

    @staticmethod
    def get_default(place_holder=""):
        return NullFlavour("unknown", "253", "openehr", place_holder)

    def _as_dict(self) -> Dict:
        flat = {
            "/_null_flavour|value": self.value,
            "/_null_flavour|code": self.code,
            "/_null_flavour|terminology": self.terminology,
        }
        if self.place_holder is not None:
            flat[""] = self.place_holder
        return flat

    def __getitem__(self, k):
        return self._as_dict()[k]

    def __setitem__(self, k, v):
        raise NotImplementedError()

    def items(self):
        return self._as_dict().items()

    def keys(self):
        return self._as_dict().keys()

    def values(self):
        return self._as_dict().values()


class _Node(abc.ABC):
    @property
    @abc.abstractmethod
    def children(self: TNode) -> List[TNode]:
        ...

    @property
    @abc.abstractmethod
    def parent(self: TNode) -> TNode:
        ...

    @property
    @abc.abstractmethod
    def path(self: TNode) -> Tuple[TNode, ...]:
        ...

    @property
    @abc.abstractmethod
    def ancestors(self: TNode) -> Tuple[TNode, ...]:
        ...

    @property
    @abc.abstractmethod
    def is_leaf(self) -> bool:
        ...

    @abc.abstractmethod
    def walk_to(self, dest: TNode) -> TNode:
        ...

    @abc.abstractmethod
    def get(self: TNode, path: str) -> TNode:
        ...

    @property
    @abc.abstractmethod
    def leaves(self: TNode) -> List[TNode]:
        ...

    @abc.abstractmethod
    def find(self: TNode, _id: str) -> Sequence[TNode]:
        ...


class Template:
    def __init__(self, root: "TemplateNode"):
        self._root = root

    @property
    def root(self) -> "TemplateNode":
        return self._root

    def __getitem__(self, path: str) -> "TemplateNode":
        path = os.path.relpath(path, self.root._id)
        return cast(TemplateNode, self.root.get(path))

    def get_conf_skeleton(self) -> str:
        conf_skeleton = set()
        indent = "  "
        for leaf in self.root.leaves:
            if leaf.in_context:
                path = f"{indent}ctx/{leaf._id}:"
            else:
                path = f"{indent}{str(leaf)}:"
            path += f" # {'NOT' if not leaf.required else ''} required"
            path += f"\n{indent}{indent}maps_to: []"
            suffixes = []
            if leaf.inputs:
                for _input in leaf.inputs:
                    if "suffix" in _input:
                        suffixes.append(f"|{_input['suffix']}:")
            if suffixes:
                path += f"\n{indent}{indent}{indent}".join(
                    [f"\n{indent}{indent}suffixes:"] + suffixes
                )

            conf_skeleton.add(path)
        return "\n".join(["paths:"] + sorted(list(conf_skeleton)))


@dataclass
class TemplateNode(_Node, abc.ABC):
    _id: str
    rm_type: str
    aql_path: str
    required: bool
    inf_cardinality: bool
    in_context: bool
    annotations: Tuple[Dict[str, str], ...] = ()
    inputs: Tuple[Dict[str, str], ...] = ()

    @property
    @abc.abstractmethod
    def default(self) -> str:
        ...

    @abc.abstractmethod
    def json(self) -> Dict:
        ...


def remove_cardinality(path: str) -> str:
    return re.sub(r"(:[0-9]+)", "", path)


def to_string(
    node: TemplateNode,
    relative_to: Optional[TemplateNode] = None,
    wildcard: bool = False,
) -> TemplatePath:
    nodes = (
        node.ancestors + (node,) if relative_to is None else relative_to.walk_to(node)
    )
    path = "/".join(
        nodes | map(lambda n: f"{n._id}:*" if n.inf_cardinality and wildcard else n._id)
    )
    return TemplatePath(path)


class Composition:
    def __init__(
        self,
        template: "Template",
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
    def template(self) -> "Template":
        return self._template

    def __getitem__(
        self, path: str
    ) -> Union["CompositionNode", List["CompositionNode"]]:
        path = path.replace(self._root._id, "", 1).strip("/")
        return self._root[path]

    def __setitem__(self, path, value: Union[Dict, "CompositionNode"]):
        path = self._remove_root_path(path)
        self._root[path] = value

    def add(self, path: str) -> str:
        path = self._remove_root_path(path)
        return self._root.add(path)

    def _remove_root_path(self, path: str) -> str:
        return re.sub(f"(\/?{self._root._id}/)", "", path)

    def set_defaults(self):
        self.root.set_defaults()

    #      for path in self.get_required_leaves():
    #          try:
    #              self[path] = self.template[path].default
    #          except InvalidDefault as ex:
    #              logger.error(ex)
    #
    #  def get_required_leaves(self, _id: Optional[str] = None) -> List[str]:
    #      return [
    #          os.path.join(self._root._id, path)
    #          for path in self._root.get_required_leaves(_id)
    #      ]


@dataclass
class CompositionNode(_Node, abc.ABC):
    template: "TemplateNode"
    value: Optional[Dict] = None
    null_flavour: Optional[NullFlavour] = None

    def __post_init__(self):
        self._id = self.template._id

        ...

    @abc.abstractmethod
    def __getitem__(self, path) -> Union["CompositionNode", List["CompositionNode"]]:
        ...

    @abc.abstractmethod
    def __setitem__(self, path, value: Union[Dict, "CompositionNode"]):
        ...

    @_Node.parent.setter
    @abc.abstractmethod
    def parent(self, value: "CompositionNode"):
        ...

    @abc.abstractmethod
    def add(self, path: str) -> str:
        ...

    #  @abc.abstractmethod
    #  def get_required_leaves(self, _id: Optional[str] = None) -> List[str]:
    #      ...

    @abc.abstractmethod
    def set_defaults(self):
        ...


class NotaLeaf(Exception):
    ...


class IncompatibleDataType(Exception):
    ...


class InvalidDefault(Exception):
    ...


def flat(
    composition: Composition, ctx: Optional[Dict[str, Dict[str, str]]] = None
) -> Dict[str, str]:
    dct = {}
    value_dicts = {
        str(leaf): leaf.value
        for leaf in composition.root.leaves
        if leaf.value is not None
    }
    value_dicts.update(ctx or {})
    for _id, suffixes in value_dicts.items():
        for suffix, value in suffixes.items():
            dct[_id + suffix] = value
    return dct
