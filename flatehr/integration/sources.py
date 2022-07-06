import abc
from itertools import repeat
from typing import (
    IO,
    Generic,
    Iterator,
    NewType,
    Sequence,
    Union,
)

from lxml import etree
from lxml.etree import _Element
from pipe import chain, map, sort

from flatehr.integration import K, V, Message


XPath = NewType("XPath", str)


class Source(abc.ABC, Generic[K, V]):
    @abc.abstractmethod
    def iter() -> Iterator[Message[K, V]]:
        ...


class XPathSource(Source[XPath, str]):
    def __init__(
        self,
        paths: Sequence[XPath],
        _input: Union[IO, str],
    ) -> None:
        self._paths = paths
        self._input = _input

    def iter(self) -> Iterator[Message[XPath, str]]:
        tree = etree.parse(self._input)

        ns = tree.getroot().nsmap
        ns["ns"] = ns.pop(None)

        mappings = (
            self._paths
            | map(
                lambda path: list(
                    zip(
                        repeat(path),
                        tree.xpath(path, namespaces=ns),
                    )
                )
            )
            | chain
            | sort(
                lambda el: el[1].sourceline
                if isinstance(el[1], _Element)
                else el[1].getparent().sourceline
            )
            | map(
                lambda el: Message(
                    key=el[0],
                    value=None if isinstance(el[1], _Element) else el[1],
                )
            )
        )
        for mapping in mappings:
            yield mapping
