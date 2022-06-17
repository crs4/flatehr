import abc
from itertools import repeat
from typing import IO, Any, Dict, Iterable, Iterator, NewType, Optional, Tuple, Union

from lxml import etree
from pipe import chain, map, sort

from flatehr.converters import Converter
from flatehr.data_types import DATA_VALUE

SourcePath = NewType("SourcePath", str)
DestPath = NewType("DestPath", str)


class Mapping(abc.ABC):
    @abc.abstractmethod
    def get_values(
        self, input_: Union[IO, str]
    ) -> Iterator[Tuple[DestPath, Optional[DATA_VALUE]]]:
        ...


class XPathMapping(Mapping):
    def __init__(
        self,
        mapping: Dict[SourcePath, DestPath],
        converter: Optional[Converter] = None,
    ) -> None:
        self._mapping = mapping
        self._converter = converter

    def get_values(
        self, input_: Union[IO, str]
    ) -> Iterator[Tuple[DestPath, Optional[DATA_VALUE]]]:
        tree = etree.parse(input_)
        ns = tree.getroot().nsmap
        elements = (
            list(self._mapping.items())
            | map(
                lambda items: list(
                    zip(
                        repeat(items[0]),
                        repeat(items[1]),
                        tree.findall(items[0], namespaces=ns),
                    )
                )
            )
            | chain
            | sort(lambda el: el[2].sourceline)
            | map(
                lambda el: (
                    el[1],
                    None
                    if len(el[2].getchildren())
                    else el[2].text
                    if not self._converter
                    else self._converter.convert(el[1], el[2].text),
                )
            )
        )
        for el in elements:
            yield el


class Converter(abc.ABC):
    @abc.abstractmethod
    def convert(self, source_path: SourcePath, value) -> Any:
        ...
