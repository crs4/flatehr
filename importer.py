import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, TextIO

from lxml import etree


def map_aqlpath_to_id(web_template: Dict) -> Dict:
    mapping = {}

    def _recursive_map_aqlpath_to_id(node, parent_mapping):
        mapping_value = os.path.join(parent_mapping, node['id'])
        mapping[node['aqlPath']] = mapping_value
        children = node.get('children', [])
        for child in children:
            _recursive_map_aqlpath_to_id(child, mapping_value)

    node = web_template['webTemplate']['tree']
    _recursive_map_aqlpath_to_id(node, "")
    return mapping


def get_annotations(opt: TextIO) -> Dict:
    tree = etree.parse(opt)
    annotation_items = tree.xpath(
        "n:annotations/n:items[@id='XSD label']",
        namespaces={'n': "http://schemas.openehr.org/v1"})
    mapping = {}
    for item in annotation_items:
        mapping[item.getparent().get('path')] = item.text
    return mapping


def get_tree(web_template: Dict) -> Dict:
    def _recursive_get_tree(node, _tree):
        _tree[node['id']] = {
            'multiple_values': node['max'] == -1,
            'children': {}
        }
        children = node.get('children', [])
        for child in children:
            _recursive_get_tree(child, _tree[node['id']]['children'])
        return _tree

    node = web_template['webTemplate']['tree']
    return _recursive_get_tree(node, {})


class Node:
    def __init__(self, path: str, tree: Dict):
        self._path = path
        self._tree = tree
        self._counter = defaultdict(int)

    @property
    def path(self):
        return self._path

    def _generate_path(self, path):
        res = ''
        tree = self._tree
        splitted_path = path.split('/')
        print(splitted_path)
        for idx, el in enumerate(splitted_path):
            if not tree[el]['multiple_values']:
                res = os.path.join(res, el)
            else:
                subpath = '/'.join(splitted_path[:idx])

                res = os.path.join(res, f'{el}:{self._counter[subpath]}')
                self._counter[subpath] += 1
            tree = tree[el]['children']
        return res, tree

    def add_node(self, path: str) -> "Node":
        path_to_remove = self._path.rsplit(
            ':', 1)[0] + '/' if self._path else self._path
        relative_path = path.replace(path_to_remove, '')
        #  relative_path = path.replace(self._path, '')
        path, tree = self._generate_path(relative_path)
        final_path = os.path.join(self._path, path)
        return Node(final_path, tree)

    def __str__(self):
        return self._path

    def __repr__(self):
        return f'{type(self)}, path "{self._path}"'


def traverse(el, root, mapping, schema):
    def _traverse(_el, _root, _nodes):
        if isinstance(_el.tag, str):
            tag = _el.tag.replace(f'{{{schema}}}', "")
            if tag in mapping:
                path = None
                if isinstance(mapping[tag], str):
                    path = mapping[tag]
                    node = _root.add_node(path)
                    _nodes[node.path] = _el.text
                else:
                    attr = list(mapping[tag].keys())[0]
                    attr_value = _el.get(attr)
                    path = mapping[tag][attr].get(attr_value)
                    print('path', path)
                    if path:
                        node = _root.add_node(path)
                        print(node._tree)
                        _root = node

        for child in _el.getchildren():
            _traverse(child, _root, _nodes)

    nodes = {}
    _traverse(el, root, nodes)
    return nodes


#  class Importer:
#      def __init__(input_file: TextIO, web_template: TextIO, mapping: TextIO):
