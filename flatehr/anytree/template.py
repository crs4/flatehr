import logging
import os
import re
from functools import singledispatchmethod
from typing import Any, Dict, List, Tuple, Optional

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
from dataclasses import dataclass

logger = logging.getLogger("flatehr")


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
        node = _recursive_create(tree)
        return Template(node)


@dataclass
class TemplateNode(Node, BaseTemplateNode):
    rm_type: str
    aql_path: str
    required: bool
    inf_cardinality: bool
    annotations: Optional[Dict[str, Any]] = None
    inputs: Optional[Dict[str, Any]] = None
