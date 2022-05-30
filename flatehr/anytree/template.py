import logging
import os
import re
from functools import singledispatchmethod
from typing import Dict, List, Tuple

import anytree
from deepdiff import DeepDiff

from flatehr.anytree._node import Node
from flatehr.composition import Composition as BaseComposition
from flatehr.composition import CompositionNode as BaseCompositionNode
from flatehr.data_types import DataValue, Factory, NullFlavour
from flatehr.template import Template
from flatehr.factory import template_factory
from flatehr.template import TemplateNode as BaseTemplateNode
from flatehr.template import WebTemplate

logger = logging.getLogger("flatehr")


@template_factory.register("anytree")
class TemplateFactory:
    def __init__(self, web_template: WebTemplate):
        self._web_template = web_template

    def get(self) -> Template:
        def _recursive_create(web_template_el):
            _node = anytree.Node(
                web_template_el["id"],
                rm_type=web_template_el["rmType"],
                required=web_template_el["min"] == 1,
                inf_cardinality=web_template_el["max"] == -1,
                annotations=web_template_el.get("annotations", {}),
                inputs=web_template_el.get("inputs"),
                aql_path=web_template_el.get("aqlPath"),
            )

            children = []
            for child in web_template_el.get("children", []):
                children.append(_recursive_create(child))
            _node.children = children

            return _node

        tree = self._web_template["tree"]
        anytree_node = _recursive_create(tree)
        return Template(TemplateNode(Node(anytree_node)))


class TemplateNode(BaseTemplateNode):
    def __init__(self, node: Node):
        self._node = node

    @property
    def rm_type(self):
        return self._node.attrs["rm_type"]

    @property
    def _id(self):
        return self._node.name

    @property
    def aql_path(self):
        return self._node.attrs["aql_path"]

    @property
    def required(self):
        return self._node.attrs["required"]

    @property
    def inf_cardinality(self):
        return self._node.attrs["inf_cardinality"]

    @property
    def annotations(self):
        return self._node.attrs["annotations"]

    @property
    def children(self):
        return [TemplateNode(child) for child in self._node.children]

    @property
    def inputs(self):
        return self._node.attrs["inputs"]

    #  def __str__(self):
    #      return f"{self.path}, rm_type={self.rm_type}, cardinality={int(self.required)}:{ '*' if self.inf_cardinality else 1 }"

    #  def __repr__(self):
    #      return f"{self.__class__.__name__}({str(self)})"

    @property
    def parent(self):
        return TemplateNode(self._node.parent)

    @property
    def ancestors(self) -> List[BaseTemplateNode]:
        return [TemplateNode(ancestor) for ancestor in self._node.ancestors]

    @property
    def path(self) -> str:
        nodes_ids = [node._id for node in self.ancestors + [self]]
        return os.path.join(*nodes_ids)

    def get_descendant(self, path: str) -> BaseTemplateNode:
        return TemplateNode(self._node.get_descendant(path))

    @property
    def is_leaf(self) -> bool:
        return self._node.is_leaf
