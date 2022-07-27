import re
from itertools import repeat
from typing import IO, Iterator, Optional, Sequence, Tuple

from lxml import etree
from lxml.etree import _Element
from pipe import chain, map, sort


XPath = str


def xpath_value_map(
    paths: Sequence[XPath], _input: IO, group_by: Optional[XPath] = None
) -> Iterator[Tuple[XPath, Optional[str]]]:
    def get_xml_element(xpath_result):
        return (
            xpath_result
            if isinstance(xpath_result, _Element)
            else xpath_result.getparent()
        )

    _input = _input
    tree = etree.parse(_input)
    ns_func = etree.FunctionNamespace(None)

    def first(context):
        return context.context_node[0]

    ns_func["first"] = first

    root = tree.getroot()
    ns = root.nsmap
    ns["ns"] = ns.pop(None)

    group_by = group_by or re.sub("{.*}", "", f"ancestor::ns:{root.tag}")
    mappings = (
        paths
        | map(
            lambda path: list(
                zip(
                    repeat(path),
                    tree.xpath(path, namespaces=ns),
                )
            )
        )
        | chain
        | sort(lambda el: get_xml_element(el[1]).sourceline)
        | map(lambda el: (el[0], None if isinstance(el[1], _Element) else el[1]))
    )

    for mapping in mappings:
        yield mapping
