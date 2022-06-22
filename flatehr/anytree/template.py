import logging
from dataclasses import dataclass
from typing import cast


from flatehr.anytree._node import Node
from flatehr.composition import InvalidDefault
from flatehr.factory import template_factory
from flatehr.rm import RMObject, get_model_class
from flatehr.template import Template
from flatehr.template import TemplateNode as BaseTemplateNode
from flatehr.template import WebTemplate, remove_cardinality

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
