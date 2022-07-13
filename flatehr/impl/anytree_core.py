import logging
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union, cast

import anytree
from pipe import chain, map, traverse

from flatehr.core import Composition
from flatehr.core import CompositionNode as BaseCompositionNode
from flatehr.core import InvalidDefault, Template
from flatehr.core import TemplateNode as BaseTemplateNode
from flatehr.core import WebTemplate, remove_cardinality, to_string
from flatehr.factory import composition_factory, template_factory
from flatehr.rm import RMObject, get_model_class


logger = logging.getLogger(__name__)


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


@template_factory.register("anytree")
class TemplateFactory:
    def __init__(self, web_template: WebTemplate):
        self._web_template = web_template

    def get(self) -> Template:
        def _recursive_create(web_template_el):
            _node = TemplateNode(
                _id=web_template_el["id"],
                rm_type=web_template_el["rmType"],
                required=web_template_el["min"] == 1,
                inf_cardinality=web_template_el["max"] == -1,
                annotations=web_template_el.get("annotations", ()),
                inputs=web_template_el.get("inputs", ()),
                aql_path=web_template_el.get("aqlPath"),
            )

            children = []
            for child in web_template_el.get("children", []):
                children.append(_recursive_create(child))
            _node.children = children

            return _node

        tree = self._web_template["tree"]
        node = _recursive_create(tree)
        return Template(node)


@dataclass
class TemplateNode(Node, BaseTemplateNode):
    def get(self, path: str) -> BaseTemplateNode:
        return cast(TemplateNode, super().get(remove_cardinality(path)))

    @property
    def default(self) -> RMObject:
        try:
            value = self.inputs[0]["defaultValue"]
        except (IndexError, KeyError) as ex:
            raise InvalidDefault(f"path {self} has no valid default") from ex

        return get_model_class(self.rm_type)(value=value)


@composition_factory.register("anytree")
class CompositionFactory:
    def __init__(self, template: Template):
        self._template = template

    def get(self) -> Composition:
        template_root = self._template.root
        composition_root = CompositionNode(template_root)
        return Composition(self._template, composition_root)


class CompositionNode(Node, BaseCompositionNode):
    def __init__(
        self, template: TemplateNode, parent: Optional["CompositionNode"] = None
    ):
        if parent and template.inf_cardinality:
            cardinality = len(cast(list, parent.get(f"{template._id}:*")))
            _id = f"{template._id}:{cardinality}"
        else:
            _id = template._id

        Node.__init__(self, _id=_id)
        BaseCompositionNode.__init__(self, template)
        Node.parent.fset(self, parent)

    def get(self, path) -> "CompositionNode":
        return cast(CompositionNode, Node.get(self, path))

    def __getitem__(self, path: str) -> Union[List[RMObject], RMObject]:
        nodes = self.get(path)
        return (
            [node.value for node in nodes] if isinstance(nodes, list) else nodes.value
        )

    def get_required_leaves(self, _id: Optional[str] = None) -> List[str]:
        not_leaves = anytree.iterators.preorderiter.PreOrderIter(
            self,
            filter_=lambda node: not node.template.is_leaf,
        )
        missing_required = (
            not_leaves
            | map(
                lambda node: anytree.iterators.preorderiter.PreOrderIter(
                    node.template,
                    stop=lambda n: not n.required if n != node.template else False,
                    filter_=lambda n: n.is_leaf
                    and n.required
                    and (n._id == _id if _id else True),
                )
            )
            | chain
        )
        missing_required_leaves = (
            missing_required
            | map(
                lambda template: os.path.relpath(
                    to_string(template, wildcard=True), self._id
                )
            )
            | traverse
        )
        return list(missing_required_leaves)

    def __setitem__(self, path, value: RMObject):

        if path.startswith("**"):
            _id = os.path.basename(path)

            missing_required_parents = (
                self.get_required_leaves(_id)
                | map(lambda path: self._get_or_create_node(os.path.dirname(path)))
            ) | traverse
            list(
                missing_required_parents
                | map(lambda node: node.__setitem__(os.path.basename(path), value))
            )
            return

        nodes = self._get_or_create_node(path)
        if not isinstance(nodes, list):
            nodes = [nodes]
        for node in nodes:
            if node.template.is_leaf:

                # @fixme: not work in case of abstract classes
                # if not isinstance(value, get_model_class(node.template.rm_type)):
                #     raise IncompatibleDataType(
                #         f"Expected value as instance of {node.template.rm_type}, found {type(value)} instead"
                #     )
                node.value = value

    def _get_or_create_node(self, path: str) -> "CompositionNode":
        if not path:
            return self
        try:
            return cast("CompositionNode", self.get(path))
        except NodeNotFound as ex:
            last_node = cast(CompositionNode, ex.node)
            missing_child_template = last_node.template.get(ex.child)

            if missing_child_template.inf_cardinality:
                cardinality = (
                    len(cast(list, last_node.get(f"{missing_child_template._id}:*")))
                    - 1
                )
                if cardinality < 0:
                    missing_child = CompositionNode(missing_child_template, last_node)
                else:
                    missing_child = last_node.get(
                        f"{missing_child_template._id}:{cardinality}"
                    )
            else:
                missing_child = CompositionNode(missing_child_template, last_node)

            remaining_path = path.replace(
                to_string(missing_child_template, relative_to=self.template),
                "",
                1,
            ).strip(self.separator)
            return missing_child._get_or_create_node(remaining_path)

    @property
    def parent(self) -> "CompositionNode":
        return cast("CompositionNode", Node.parent.fget(self))

    def add(self, path: str) -> str:
        parent = cast(
            "CompositionNode",
            self._get_or_create_node(os.path.dirname(path.rstrip("/"))),
        )
        node = CompositionNode(self.template.get(path), parent)
        return str(node)
