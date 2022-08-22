from itertools import repeat
from typing import IO, Iterator, Optional, Sequence, Tuple

from lxml import etree
from lxml.etree import _Element
from pipe import chain, map, sort

from flatehr.sources.base import Source, Key, Value


XPath = str


class Element:
    def __init__(self, base_element: _Element):
        self._element = base_element


class XPathSource(Source):
    def __init__(
        self,
        input_file: IO,
        paths: Sequence[XPath],
        relative_root: Optional[Element] = None,
    ):
        self._input_file = input_file
        self._paths = paths
        self._relative_root = relative_root
        self._tree = etree.parse(self._input_file)
        self._ns_func = etree.FunctionNamespace(None)
        self._ns = self.root._element.nsmap
        self._ns["ns"] = self._ns.pop(None)

        def first(context):
            return context.context_node[0]

        self._ns_func["first"] = first

    @property
    def root(self):
        return Element(self._tree.getroot())

    def get_elements(self, path: XPath) -> Sequence[Element]:
        return [Element(_) for _ in self._tree.xpath(path, namespaces=self._ns)]

    @property
    def relative_root(self) -> Optional[Element]:
        return self._relative_root

    @relative_root.setter
    def relative_root(self, element: Element):
        self._relative_root = element

    def iter(self) -> Iterator[Tuple[Key, Value]]:
        def get_xml_element(xpath_result):
            return (
                xpath_result
                if isinstance(xpath_result, _Element)
                else xpath_result.getparent()
            )

        root = self._tree.getroot()

        relative_root = (
            self.relative_root._element if self.relative_root is not None else root
        )

        mappings = (
            self._paths
            | map(
                lambda path: list(
                    zip(
                        repeat(path),
                        relative_root.xpath(path, namespaces=self._ns),
                    )
                )
            )
            | chain
            | sort(lambda el: get_xml_element(el[1]).sourceline)
            | map(lambda el: (el[0], None if isinstance(el[1], _Element) else el[1]))
        )

        for mapping in mappings:
            yield mapping
