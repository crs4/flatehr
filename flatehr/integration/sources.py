import abc
from itertools import repeat
from typing import (
    IO,
    Dict,
    Generic,
    Iterator,
    NewType,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

from lxml import etree
from lxml.etree import _Element
from pipe import chain, map, sort

from flatehr.integration import K, V, Message


XPath = str
T = TypeVar("T")


class Source(abc.ABC, Generic[T]):
    @abc.abstractmethod
    def __call__() -> Iterator[T]:
        ...


class XPathSource(Source[Tuple[XPath, Optional[str]]]):
    def __init__(
        self,
        paths: Sequence[XPath],
        _input: Union[IO, str],
    ) -> None:
        self._paths = paths
        self._input = _input
        self._tree = etree.parse(self._input)

    def __call__(self) -> Iterator[Tuple[XPath, Optional[str]]]:

        ns = self._tree.getroot().nsmap
        ns["ns"] = ns.pop(None)

        mappings = (
            self._paths
            | map(
                lambda path: list(
                    zip(
                        repeat(path),
                        self._tree.xpath(path, namespaces=ns),
                    )
                )
            )
            | chain
            | sort(
                lambda el: el[1].sourceline
                if isinstance(el[1], _Element)
                else el[1].getparent().sourceline
            )
            | map(lambda el: (el[0], None if isinstance(el[1], _Element) else el[1]))
        )
        for mapping in mappings:
            yield mapping
