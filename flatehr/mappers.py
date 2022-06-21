import abc
from itertools import repeat
from typing import Dict, IO, Iterator, NewType, Optional, Tuple, Union

from lxml import etree
from pipe import chain, map, sort

from flatehr.converters import Converter
from flatehr.rm.models import DVText, RMObject

SourcePath = NewType("SourcePath", str)
DestPath = NewType("DestPath", str)


class Mapping(abc.ABC):
    @abc.abstractmethod
    def get_values(
        self, input_: Union[IO, str]
    ) -> Iterator[Tuple[DestPath, Optional[RMObject]]]:
        ...


class XPathMapping(Mapping):
    def __init__(
        self,
        mapping: Dict[SourcePath, DestPath],
        converter: Optional[Converter] = None,
    ) -> None:
        self._mapping = mapping
        self._convert = converter.convert if converter else lambda _, v: DVText(value=v)

    def get_values(
        self, input_: Union[IO, str]
    ) -> Iterator[Tuple[DestPath, Optional[RMObject]]]:
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
                    else self._convert(el[1], el[2].text),
                )
            )
        )
        for el in elements:
            yield el
