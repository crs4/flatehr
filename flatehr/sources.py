import abc
from itertools import repeat
from typing import IO, Dict, Iterator, NamedTuple, NewType, Optional, Tuple, Union

from lxml import etree
from lxml.etree import _Element
from pipe import chain, map, sort

from flatehr.template import Template, TemplateNode, TemplatePath

XPath = NewType("XPath", str)
Value = Union[str, int, float, Dict]


class Mapping(NamedTuple):
    template_node: TemplateNode
    value: Optional[Value] = None


class Source(abc.ABC):
    @abc.abstractmethod
    def iter() -> Iterator[Mapping]:
        ...


class XPathSource(Source):
    def __init__(
        self,
        template: Template,
        mapping: Dict[XPath, TemplatePath],
        _input: Union[IO, str],
    ) -> None:
        self._mapping = mapping
        self._template = template
        self._input = _input

    def iter(self) -> Iterator[Mapping]:
        tree = etree.parse(self._input)

        ns = tree.getroot().nsmap
        ns["ns"] = ns.pop(None)

        mappings = (
            list(self._mapping.items())
            | map(
                lambda items: list(
                    zip(
                        repeat(items[0]),
                        repeat(items[1]),
                        tree.xpath(items[0], namespaces=ns),
                    )
                )
            )
            | chain
            | sort(
                lambda el: el[2].sourceline
                if isinstance(el[2], _Element)
                else el[2].getparent().sourceline
            )
            | map(
                lambda el: Mapping(
                    template_node=self._template[el[1]],
                    value=None if isinstance(el[2], _Element) else el[2],
                )
            )
        )
        for mapping in mappings:
            yield mapping
