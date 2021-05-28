import abc
import logging
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from lxml.etree import _Element

logger = logging.getLogger()


@dataclass
class WebTemplateNode:
    path: str
    rm_type: str
    required: bool
    inf_cardinality: bool
    annotations: Dict = None
    children: List["WebTemplateNode"] = None

    def __post_init__(self):
        self.annotations = self.annotations or {}
        self.children = self.children or []

    @staticmethod
    def create(web_template: Dict) -> "WebTemplateNode":
        def _recursive_create(web_template_el: Dict, parent_path: str = ''):
            path = os.path.join(parent_path, web_template_el['id'])
            node = WebTemplateNode(path, web_template_el['rmType'],
                                   web_template_el['min'] == 1,
                                   web_template_el['max'] == -1,
                                   web_template_el.get('annotations', {}), [])

            children = web_template_el.get('children', [])
            for child in children:
                node.children.append(_recursive_create(child, path))

            return node

        tree = web_template['tree']
        return _recursive_create(tree)

    def get_child(self, path):
        for child in self.children:
            child_path_splitted = child.path.split('/')
            logger.debug('path to find %s, child path splitted %s', path,
                         child_path_splitted)

            if child_path_splitted[-1] == path:
                logger.debug('found child with path %s', child.path)
                return child
        raise WebTemplateNode.NotFound(path)

    class NotFound(Exception):
        pass


class CompositionNode:
    def __init__(self, path: str, web_template: WebTemplateNode):
        self._path = path
        self._web_template = web_template
        self._counter = defaultdict(int)

    @property
    def web_template(self):
        return self._web_template

    @property
    def path(self):
        return self._path

    def add_node(self, path: str) -> "CompositionNode":
        logger.debug('add node %s to node  %s', path, self._path)
        path_to_remove = self._path.rsplit(
            ':', 1)[0] + '/' if self._path else self._path
        relative_path = path.replace(path_to_remove, '')
        path, tree = self._generate_path(relative_path)
        final_path = os.path.join(self._path, path)
        return CompositionNode(final_path, tree)

    def _generate_path(self, path):
        res = ''
        tree = self._web_template
        splitted_path = path.split('/')
        logger.debug('splitted_path %s', splitted_path)
        for idx, el in enumerate(splitted_path):
            logger.debug('subpath %s', el)
            if not tree.inf_cardinality:
                res = os.path.join(res, el)
            else:
                logger.debug('inf cardinality')
                subpath = '/'.join(splitted_path[:idx])

                #  res = os.path.join(res, f'{el}:{self._counter[subpath]}')
                res = os.path.join(f'{res}:0', el)
                #  self._counter[el] += 1
            tree = tree.get_child(el)
        return res, tree

    def __str__(self):
        return self._path

    def __repr__(self):
        return f'{type(self)}, path "{self._path}"'


class CompositionFactory(abc.ABC):
    @abc.abstractmethod
    def get_composition(self, source: Any) -> Dict:
        ...


class Composition:
    def __init__(self, value_converter: Dict[str, Callable]):
        self._dict = {}
        self._converter = value_converter

    def add_node(self, node: CompositionNode, value):
        self._dict[node.path] = self._converter.get(node.web_template.rm_type,
                                                    lambda x: x)(value)

    def as_dict(self):
        return self._dict


class XmlToCompositionFactory(CompositionFactory):
    def __init__(self,
                 web_template: WebTemplateNode,
                 defaults: Dict[str, str] = None,
                 value_converter: Dict[str, Callable] = None):
        self.web_template = web_template
        self.defaults = defaults or {}
        self.value_converter = value_converter or {}
        self._mapping = self._get_mapping(web_template)

    @staticmethod
    def _get_mapping(web_template: Dict) -> Dict:
        def _recursive_get_mapping(_node, _mapping):
            try:
                _mapping[_node.annotations["XSD label"]] = _node.path
                logger.debug('add mapping %s -> %s ',
                             _node.annotations["XSD label"], _node.path)
            except KeyError:
                pass
                #  logger.debug('skipping node %s, no annotations', path)
            for child in _node.children:
                _recursive_get_mapping(child, _mapping)

        mapping = {}
        _recursive_get_mapping(web_template, mapping)
        return mapping

    def get_composition(self, source: _Element) -> Composition:
        namespace = source.getroottree().getroot().nsmap[None]

        def _traverse(xml_el, composition_node: CompositionNode,
                      _composition: Composition):
            if isinstance(xml_el.tag, str):
                tag = xml_el.tag.replace(f'{{{namespace}}}', "")
                if tag in self._mapping:
                    path = None
                    if isinstance(self._mapping[tag], str):
                        path = self._mapping[tag]
                        node = composition_node.add_node(path)
                        _composition.add_node(node, xml_el.text)
                    else:
                        attr = list(self._mapping[tag].keys())[0]
                        attr_value = xml_el.get(attr)
                        path = self._mapping[tag][attr].get(attr_value)
                        if path:
                            node = composition_node.add_node(path)
                            composition_node = node

            for child in xml_el.getchildren():
                _traverse(child, composition_node, _composition)

        composition = Composition(self.value_converter)
        _traverse(source,
                  CompositionNode(self.web_template.path, self.web_template),
                  composition)
        return composition


def _get_required(web_template: Dict) -> Dict:
    root = web_template['tree']
    required = {}

    def _get_required(node, _parent, _parent_path):
        node_path = node['aqlPath']
        children = node.get('children', [])

        node_annotations = node.get("annotations", {})
        if "XSD label" not in node_annotations:
            if node['min'] == 1 and not children:
                required[
                    node_path] = None if _parent['min'] == 1 else _parent_path
        for child in children:
            _get_required(child, node, node_path)

    for child in root['children']:
        _get_required(child, root, '')

    return required


if __name__ == '__main__':
    import json
    import requests
    from lxml import etree
    from requests.auth import HTTPBasicAuth

    logging.basicConfig(
        level=logging.INFO,
        format=' {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s')

    value_converter = {
        'DV_DURATION': lambda x: f'P0Y{x}W0DT0H0M0S',
        'DV_BOOLEAN': lambda x: str(bool(x))
    }

    xtree = etree.parse(open('import_example.xml', 'r'))
    webt = WebTemplateNode.create(json.load(open('crc_cohort.json', 'r')))
    factory = XmlToCompositionFactory(webt, value_converter=value_converter)
    patient = xtree.xpath(
        '//n:BHPatient',
        namespaces={'n': "http://registry.samply.de/schemata/import_v1"})[0]
    comp = factory.get_composition(patient)
    resp = requests.post(
        'http://localhost:8080/ehrbase/rest/ecis/v1/composition/?format=FLAT&ehrId=1d62ef84-54f7-49ee-bfe6-c6675b46d960&templateId=crc_cohort',
        json=comp.as_dict(),
        auth=HTTPBasicAuth('ehrbase-user', 'SuperSecretPassword'))
    print(resp.json())
