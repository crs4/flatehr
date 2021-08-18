import os
import re
from typing import Dict, Tuple

import anytree

from flatehr.data_types import DataValue, factory


class Node:
    def __init__(self, node: anytree.Node):
        self._node = node

    def __str__(self):
        return str(self._node)

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
            yield type(self)(leaf)

    def walk_to(self, node: "Node") -> Tuple:
        walker = anytree.walker.Walker()
        return tuple(
            type(self)(node_)
            for node_ in walker.walk(self._node, node._node)[2])

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
                                 inf_cardinality=web_template_el['max'] == -1,
                                 annotations=web_template_el.get(
                                     'annotations', {}),
                                 inputs=web_template_el.get('inputs'))

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
    def annotations(self):
        return self._node.annotations

    @property
    def children(self):
        return [WebTemplateNode(child) for child in self._node.children]

    @property
    def inputs(self):
        return self._node.inputs

    def __str__(self):
        return f'{self.path}, rm_type={self.rm_type},'\
            f'required={self.required}, inf_cardinality={self.inf_cardinality}'

    def __repr__(self):
        return f'{self.__class__.__name__}({str(self)})'


class Composition:
    def __init__(self, web_template: WebTemplateNode):
        self._web_template = web_template
        self._root = CompositionNode(
            anytree.Node(web_template.path.strip(web_template.separator)),
            web_template)

    @property
    def web_template(self):
        return self._web_template

    @property
    def root(self):
        return self._root

    def create_node(self, path, *args, **kwargs) -> "CompositionNode":
        if not os.path.isabs(path):
            path = '/' + path
        composition_node = self.root.create_node(path)
        if args or kwargs:
            value = factory(composition_node.web_template, *args, **kwargs)
            composition_node.value = value
        return composition_node

    def get(self, path) -> "CompositionNode":
        raise NotImplementedError()

    def set_default(self, name: str, *args, **kwargs) -> "CompositionNode":
        resolver = anytree.resolver.Resolver('name')
        leaves = [
            node for node in self._web_template.leaves if node.name == name
        ]
        for target in leaves:
            descendants = self._web_template.walk_to(target)[:-1]
            if not descendants:
                self._root.create_node(name, *args, **kwargs)
            else:
                path = self._root.separator.join([
                    descendant.name if descendant.inf_cardinality is False else
                    f'{descendant.name}:*' for descendant in descendants
                ])
                try:
                    for node in resolver.glob(self._root._node, path):
                        descendant_path = node.separator.join([
                            CompositionNode(node, node.web_template).path, name
                        ])

                    self._root.create_node(descendant_path, *args, **kwargs)
                except anytree.ChildResolverError:
                    ...

    def as_flat(self):
        flat = {}
        for leaf in self._root.leaves:
            if leaf.web_template.is_leaf:
                value = leaf.value.to_json()
                if isinstance(value, dict):
                    for key, value in value.items():
                        flat[
                            f'{leaf.path.strip(leaf.separator)}|{key}'] = value
                else:
                    flat[leaf.path.strip(leaf.separator)] = value
        return flat


class CompositionNode(Node):
    def __init__(self,
                 node: anytree.Node,
                 web_template_node: WebTemplateNode,
                 value: DataValue = None):
        super().__init__(node)
        self._node.web_template = web_template_node
        self._web_template_node = web_template_node
        self._resolver = anytree.Resolver('name')
        self._node.value = value

    def __repr__(self):
        return '<CompositionNode %s>' % self._node

    @property
    def web_template(self):
        return self._web_template_node

    def add_child(self, name: str, value: DataValue = None):
        web_template_node = self._web_template_node.get_descendant(name)
        if web_template_node.inf_cardinality:
            n_siblings = len(self._resolver.glob(self._node, f'{name}:*'))
            name = f'{name}:{n_siblings}'
            node = anytree.Node(name, parent=self._node)
        else:
            try:
                node = self._resolver.get(self._node, name)
            except anytree.ChildResolverError:
                node = anytree.Node(name, parent=self._node)
        return CompositionNode(node, web_template_node, value)

    def create_node(self, path: str, *args, **kwargs) -> "CompositionNode":
        def _add_descendant(root, path_, *args, **kwargs):
            try:
                node = self._resolver.get(root, path_)
            except anytree.ChildResolverError as ex:
                last_node = ex.node
                missing_child = ex.child
                web_template_node = last_node.web_template
                node = CompositionNode(
                    last_node, web_template_node).add_child(missing_child)

                path_to_remove = [n.name for n in last_node.path] + [
                    missing_child
                ] if path_.startswith('/') else [missing_child]

                for el in path_to_remove:
                    path_ = path_.replace(f'{el}', '', 1)

                path_ = path_.lstrip(root.separator)

                return _add_descendant(node._node, path_, *args, **kwargs)
            else:
                web_template_node = node.web_template
                if args or kwargs:
                    value = factory(node.web_template, *args, **kwargs)
                else:
                    value = None
                return CompositionNode(node, web_template_node, value)

        return _add_descendant(self._node, path, *args, **kwargs)

    def _get_web_template(self):
        path = re.sub(r'\[\d+\]', '', self.path)
        return self._resolver.get(self._web_template_node, path)

    @property
    def leaves(self):
        for leaf in self._node.leaves:
            yield CompositionNode(leaf, leaf.web_template, leaf.value)
