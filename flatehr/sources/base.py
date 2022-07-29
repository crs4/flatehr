import abc
from typing import Any, Iterator, OrderedDict, Tuple, Union


Key = str
Value = Any


class Source(abc.ABC):
    @abc.abstractmethod
    def iter(self) -> Iterator[Tuple[Key, Value]]:
        ...


class FlatDictSource(Source):
    def __init__(self, dct: OrderedDict[str, Union[str, float, int]]):
        self._dct = dct

    def iter(self) -> Iterator[Tuple[Key, Value]]:
        for item in self._dct.items():
            yield item
