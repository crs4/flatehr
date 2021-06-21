import re
from typing import Dict, Union

import anytree


class Node:
    def __init__(self, node: anytree.Node):
        self._node = node

    def __str__(self):
        return self._node

    def _set_value(self, value):
        self._node.value = value

    def _get_value(self):
        return self._node.value

    value = property(_get_value, _set_value)

    @property
    def is_leaf(self):
        return self._node.is_leaf

    @property
    def separator(self):
        return self._node.separator

    @property
    def name(self):
        return self._node.name

    @property
    def leaves(self):
        for leaf in self._node.leaves:
            yield CompositionNode(leaf, leaf.web_template)

    @property
    def path(self):
        return self._node.separator + self._node.separator.join(
            [n.name for n in self._node.path]) + self._node.separator

    def get_descendant(self, path: str):
        resolver = anytree.Resolver('name')
        return type(self)(resolver.get(self._node, path))


class WebTemplateNode(Node):
    @staticmethod
    def create(dct: Dict) -> "WebTemplateNode":
        def _recursive_create(web_template_el):
            _node = anytree.Node(web_template_el['id'],
                                 rm_type=web_template_el['rmType'],
                                 required=web_template_el['min'] == 1,
                                 inf_cardinality=web_template_el['max'] == -1)

            children = []
            for child in web_template_el.get('children', []):
                children.append(_recursive_create(child)._node)
            _node.children = children

            return WebTemplateNode(_node)

        tree = dct['tree']
        node = _recursive_create(tree)
        return node

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
    def __init__(self, web_template: WebTemplateNode):
        self._web_template = web_template
        self._root = CompositionNode(anytree.Node(web_template.path),
                                     web_template)

    @property
    def web_template(self):
        return self._web_template

    @property
    def root(self):
        return self._root

    def as_flat(self):
        flat = {}
        for leaf in self._root.leaves:
            if leaf.web_template.is_leaf:
                flat[leaf.path.rstrip(leaf.separator)] = leaf.value
        return flat


class CompositionNode(Node):
    def __init__(self, node: anytree.Node, web_template_node: WebTemplateNode):
        super().__init__(node)
        self._node.web_template = web_template_node
        self._web_template_node = web_template_node
        self._resolver = anytree.Resolver('name')

    def __repr__(self):
        return '<CompositionNode %s>' % self._node

    @property
    def web_template(self):
        return self._web_template_node

    def add_child(self, name):
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
                node = self._resolver.get(root, path_)
            except anytree.ChildResolverError as ex:
                last_node = ex.node
                missing_child = ex.child
                web_template_node = last_node.web_template
                node = CompositionNode(
                    last_node, web_template_node).add_child(missing_child)

                for el in [n.name for n in last_node.path] + [missing_child]:
                    path_ = path_.replace(el, '')

                path_ = path_.lstrip(root.separator)

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
    web_template = WebTemplateNode.create(webt)
    comp = Composition(web_template)
    event0 = comp.root.add_descendant(
        'molecular_markers/result_group/oncogenic_mutations_test/any_event')
    event0.add_descendant('braf_pic3ca_her2_mutation_status').value = 1
    comp.root.add_descendant(
        'molecular_markers/result_group/oncogenic_mutations_test/any_event/braf_pic3ca_her2_mutation_status'
    ).value = 2
    #  print('------------')
    #  comp.root.add_descendant(
    #      'molecular_markers/result_group/oncogenic_mutations_test/any_event/braf_pic3ca_her2_mutation_status'
    #  )
    print(comp.as_flat())
