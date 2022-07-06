import abc
from itertools import repeat
from typing import (
    Any,
    IO,
    Iterator,
    NamedTuple,
    NewType,
    Optional,
    Sequence,
    Union,
)

from lxml import etree
from lxml.etree import _Element
from pipe import chain, map, sort


XPath = NewType("XPath", str)
Value = Any
Key = NewType("Key", str)


class Message(NamedTuple):
    key: Key
    value: Optional[Value] = None


class Source(abc.ABC):
    @abc.abstractmethod
    def iter() -> Iterator[Message]:
        ...


class XPathSource(Source):
    def __init__(
        self,
        paths: Sequence[XPath],
        _input: Union[IO, str],
    ) -> None:
        self._paths = paths
        self._input = _input

    def iter(self) -> Iterator[Message]:
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
