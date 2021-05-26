import os
from collections import defaultdict
from typing import Dict
import logging

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


def get_annotations(web_template: Dict) -> Dict:
    def _get_annotations(_node, _annotations, parent_path=""):
        node_annotations = _node.get("annotations", {})
        path = os.path.join(parent_path, _node['id'])
        try:
            _annotations[node_annotations["XSD label"]] = path
            logger.info('added _annotations for node %s', path)
        except KeyError:
            logger.debug('node %s has annotations %s, skipping...', path,
                         _annotations)
        children = _node.get("children", [])
        for child in children:
            _get_annotations(child, _annotations, path)

    annotations = {}
    node = web_template['tree']
    _get_annotations(node, annotations)
    return annotations


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

    node = web_template['tree']
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
        for idx, el in enumerate(splitted_path):
            if not tree[el]['multiple_values']:
                res = os.path.join(res, el)
            else:
                subpath = '/'.join(splitted_path[:idx])

                #  res = os.path.join(res, f'{el}:{self._counter[subpath]}')
                res = os.path.join(res, f'{el}:0')
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
                    if path:
                        node = _root.add_node(path)
                        _root = node

        for child in _el.getchildren():
            _traverse(child, _root, _nodes)

    nodes = {}
    _traverse(el, root, nodes)
    return nodes


#  class Importer:
#      def __init__(input_file: TextIO, web_template: TextIO, mapping: TextIO):
