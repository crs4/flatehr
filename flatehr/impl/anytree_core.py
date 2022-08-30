from itertools import repeat
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union, cast

import anytree
from pipe import chain, filter, map

from flatehr.core import Composition
from flatehr.core import CompositionNode as BaseCompositionNode
from flatehr.core import InvalidDefault, Template
from flatehr.core import TemplateNode as BaseTemplateNode
from flatehr.core import WebTemplate, remove_cardinality, to_string

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
                in_context=web_template_el.get("inContext", False),
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
    def default(self) -> str:
        try:
            return self.inputs[0]["defaultValue"]
        except (IndexError, KeyError) as ex:
            raise InvalidDefault(f"path {self} has no valid default") from ex

    #  @fixme to complete...
    def json(self):
        return {"inputs": self.inputs}


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
        self._ctx: Dict[str, Dict[str, str]] = {}

    def get(self, path) -> "CompositionNode":
        return cast(CompositionNode, Node.get(self, path))

    def __getitem__(self, path: str) -> Union[List[Dict], Dict]:
        nodes = self.get(path)
        return (
            [node.value for node in nodes] if isinstance(nodes, list) else nodes.value
        )

    def set_defaults(self):
        def _set_defaults(node, path, inputs):

            values = {}
            for input_ in inputs:
                if "defaultValue" in input_:
                    values[
                        f"{'|' + input_['suffix'] if 'suffix' in input_ else ''}"
                    ] = input_["defaultValue"]
                    if "terminology" in input_:
                        values["|terminology"] = input_["terminology"]

            node[path] = values

        list(
            self.descendants
            | map(
                lambda n: (
                    n,
                    set(
                        [
                            child._id
                            for child in n.template.children
                            if child.required and not child.in_context
                        ]
                    )
                    - set(
                        [
                            remove_cardinality(child._id)
                            for child in n.children
                            if child.template.required and not child.template.in_context
                        ]
                    ),
                )
            )
            | filter(lambda n_set: len(n_set[1]))
            | map(lambda n_set: list(zip(repeat(n_set[0], len(n_set[1])), n_set[1])))
            | chain
            | map(
                lambda n_path: (
                    n_path[0],
                    list(
                        anytree.iterators.preorderiter.PreOrderIter(
                            n_path[0].template.get(str(n_path[1])),
                            stop=lambda n: not n.required,
                            filter_=lambda n: n.is_leaf
                            and not n.in_context
                            and n.required,
                        )
                    ),
                ),
            )
            | map(
                lambda n_path: list(zip(repeat(n_path[0], len(n_path[1])), n_path[1]))
            )
            | chain
            | map(
                lambda n_path: (
                    _set_defaults(
                        n_path[0],
                        os.path.relpath(
                            str(n_path[1]),
                            remove_cardinality(str(n_path[0])),
                        ),
                        n_path[1].inputs,
                    )
                )
            )
        )

    def __setitem__(self, path, value: Union[Dict, "CompositionNode"]):

        #  if path.startswith("**"):
        #      _id = os.path.basename(path)
        #
        #      missing_required_parents = (
        #          self.get_required_leaves(_id)
        #          | map(lambda path: self._get_or_create_node(os.path.dirname(path)))
        #      ) | traverse
        #      list(
        #          missing_required_parents
        #          | map(lambda node: node.__setitem__(os.path.basename(path), value))
        #      )
        #      return

        nodes = self._get_or_create_node(path, "*" not in path)
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

    def _get_or_create_node(
        self, path: str, append_to_last_occurence: bool = True
    ) -> "CompositionNode":
        if not path:
            return self
        try:
            return cast("CompositionNode", self.get(path))
        except NodeNotFound as ex:
            last_node = cast(CompositionNode, ex.node)
            missing_child_template = last_node.template.get(ex.child)

            if append_to_last_occurence:
                if missing_child_template.inf_cardinality:
                    cardinality = (
                        len(
                            cast(list, last_node.get(f"{missing_child_template._id}:*"))
                        )
                        - 1
                    )
                    if cardinality < 0:
                        missing_child = CompositionNode(
                            missing_child_template, last_node
                        )
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
                return missing_child._get_or_create_node(
                    remaining_path, append_to_last_occurence
                )
            else:
                last_wildcard_idx = path.rindex("*")
                try:
                    slash_after_wildcard_idx = path.index("/", last_wildcard_idx)
                except ValueError:
                    slash_after_wildcard_idx = len(path) - 1

                _path = path[:slash_after_wildcard_idx]
                remaining_path = path[slash_after_wildcard_idx:].strip("/")
                try:
                    wildcard_nodes = self._resolver.glob(self, _path)
                except anytree.ChildResolverError:
                    wildcard_nodes = []

                nodes = [
                    wildcard_node._get_or_create_node(remaining_path)
                    for wildcard_node in wildcard_nodes
                ]
                return nodes

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
