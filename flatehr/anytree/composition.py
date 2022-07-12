import logging
import os
from typing import List, Optional, Union, cast

import anytree
from pipe import chain, map, traverse

from flatehr.anytree._node import Node, NodeNotFound
from flatehr.core import Composition
from flatehr.core import CompositionNode as BaseCompositionNode
from flatehr.core import NotaLeaf, Template, TemplateNode, to_string
from flatehr.factory import composition_factory
from flatehr.rm import RMObject

logger = logging.getLogger(__name__)


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
