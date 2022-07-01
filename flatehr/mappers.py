import abc
from itertools import repeat
from typing import IO, Dict, Iterator, NewType, Optional, Tuple, Union

from lxml import etree
from lxml.etree import _Element
from pipe import chain, map, sort

from flatehr.converters import Converter
from flatehr.rm import NullFlavour
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
        strip_text: bool = True,
    ) -> None:
        self._mapping = mapping
        self._strip_text = strip_text
        self._convert = (
            converter.convert
            if converter
            else lambda _, v: DVText(value=v)
            if v
            else NullFlavour.get_default()
        )

    def get_values(
        self, input_: Union[IO, str]
    ) -> Iterator[Tuple[DestPath, Optional[RMObject]]]:
        tree = etree.parse(input_)

        ns = tree.getroot().nsmap
        ns["ns"] = ns.pop(None)

        elements = (
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
                lambda el: (
                    el[1],
                    None
                    if isinstance(el[2], _Element)
                    else self._convert(
                        el[1], el[2].strip() if self._strip_text else el[2]
                    )
                    #  None
                    #  if len(el[2].getchildren())
                    #  else self._convert(el[1], el[2].text),
                )
            )
        )
        for el in elements:
            yield el
