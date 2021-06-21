import os
import re
from pathlib import Path
from typing import Dict, Tuple, Union

import anytree
from lxml.etree import _Element


class Node:
    def __init__(self, node: anytree.Node):
        self._node = node

    def get_descendant(self, path: str):
        resolver = anytree.Resolver('name')
        return type(self)(resolver.get(self._node, path))


class WebTemplate:
    def __init__(self, dct: Dict):
        self.root, self._mapping = WebTemplateNode.create(dct)


class WebTemplateNode(Node):
    @staticmethod
    def create(dct: Dict) -> Tuple["WebTemplateNode", Dict]:
        def _recursive_create(web_template_el: Dict, mapping: Dict):
            annotations = web_template_el.get('annotations', {})
            _node = anytree.Node(web_template_el['id'],
                                 rm_type=web_template_el['rmType'],
                                 required=web_template_el['min'] == 1,
                                 inf_cardinality=web_template_el['max'] == -1)

            children = []
            try:
                mapping[annotations["XSD label"]] = _node
            except KeyError:
                pass
            for child in web_template_el.get('children', []):
                children.append(_recursive_create(child, mapping)._node)
            _node.children = children

            return WebTemplateNode(_node)

        mapping = {}
        tree = dct['tree']
        node = _recursive_create(tree, mapping)
        return node, mapping

    @property
    def path(self):
        return self._node.name

    @property
    def rm_type(self):
        return self._node.rm_type

    @property
    def required(self):
        return self._node.required

    @property
    def inf_cardinality(self):
        return self._node.inf_cardinality

    @property
    def children(self):
        return [WebTemplateNode(child) for child in self._node.children]

    def __str__(self):
        return f'{self.path}, rm_type={self.rm_type},'\
            f'required={self.required}, inf_cardinality={self.inf_cardinality}'

    def __repr__(self):
        return f'{self.__class__.__name__}({str(self)})'


class Composition:
    def __init__(self, web_template: WebTemplate):
        self._web_template = web_template
        self._root = CompositionNode(anytree.Node(web_template.root.path),
                                     web_template.root)

    @property
    def web_template(self):
        return self._web_template

    @property
    def root(self):
        return self._root


class CompositionNode:
    def __init__(self, node: anytree.Node, web_template_node: WebTemplateNode):
        self._node = node
        self._node.web_template = web_template_node
        self._web_template_node = web_template_node
        self._resolver = anytree.Resolver('name')

    def __repr__(self):
        return '<CompositionNode %s>' % self._node

    def __str__(self):
        return self._node

    @property
    def path(self):
        return '/' + self._node.separator.join(
            [n.name for n in self._node.path]) + '/'

    def add_child(self, name):
        path = os.path.join(self.path, name)
        web_template_node = self._web_template_node.get_descendant(name)
        if web_template_node.inf_cardinality:
            n_siblings = len(self._resolver.glob(self._node, f'{name}[*]'))
            name = f'{name}[{n_siblings}]'
            node = anytree.Node(name, parent=self._node)
        else:
            try:
                node = self._resolver.get(self._node, name)
            except anytree.ChildResolverError:
                node = anytree.Node(name, parent=self._node)
        return CompositionNode(node, web_template_node)

    def add_descendant(self, path):
        def _add_descendant(root, path_):
            try:
                print('--------')
                node = self._resolver.get(root, path_)
            except anytree.ChildResolverError as ex:
                last_node = ex.node
                missing_child = ex.child
                web_template_node = last_node.web_template
                node = CompositionNode(
                    last_node, web_template_node).add_child(missing_child)
                path_ = path_.replace(f'{missing_child}',
                                      '').lstrip(root.separator)

                print(node._node)
                print(path_)
                return _add_descendant(node._node, path_)
            else:
                web_template_node = node.web_template
                return CompositionNode(node, web_template_node)

        return _add_descendant(self._node, path)

    def _get_web_template(self):
        path = re.sub(r'\[\d+\]', '', self.path)
        return self._resolver.get(self._web_template_node, path)

    def set_value(self, value: Union[int, str]):
        ...


if __name__ == '__main__':
    import json
    webt = json.load(open("crc_cohort.json", 'r'))
    web_template = WebTemplate(webt)
    comp = Composition(web_template)
    comp.root.add_descendant(
        'molecular_markers/result_group/oncogenic_mutations_test/any_event/braf_pic3ca_her2_mutation_status'
    )
    print('------------')
    print(comp.root._node.descendants)
