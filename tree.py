import os
from typing import Dict, Tuple

from anytree import Node
from anytree.resolver import ChildResolverError, Resolver
from lxml.etree import _Element


def create_web_template(web_template: Dict) -> Tuple[Node, Dict]:
    def _recursive_create(web_template_el: Dict, mapping: Dict):
        annotations = web_template_el.get('annotations', {})
        _node = Node(web_template_el['id'],
                     rm_type=web_template_el['rmType'],
                     required=web_template_el['min'] == 1,
                     inf_cardinality=web_template_el['max'] == -1)

        children = []
        try:
            mapping[annotations["XSD label"]] = _node
        except KeyError:
            pass
        for child in web_template_el.get('children', []):
            children.append(_recursive_create(child, mapping))
        _node.children = children

        return _node

    mapping = {}
    tree = web_template['tree']
    node = _recursive_create(tree, mapping)
    return node, mapping


class Composition:
    def __init__(self, web_template: Node):
        self._root = Node(web_template.name)
        self._web_template = web_template

    @property
    def web_template(self):
        return self._web_template

    def set(self, path, value):
        resolver = Resolver('name')
        top_node = self._root
        web_template = self._web_template
        while path:
            try:
                node = resolver.get(top_node, path)
                node.value = value
                last_path = path
            except ChildResolverError as ex:
                last_node = ex.node
                missing_child = ex.child
                last_path = os.path.join(
                    *([n.name for n in last_node.path[1:]] + [missing_child]))
                web_template = resolver.get(web_template,
                                            os.path.join(last_path))
                if web_template.inf_cardinality:
                    nodes = resolver.glob(last_node, f'{missing_child}[*]')
                    if nodes:
                        missing_child = list(nodes)[0].name
                    else:
                        missing_child = f'{missing_child}[0]'

                top_node = Node(missing_child, parent=top_node)
            path = path.replace(last_path, '')
