import abc
from typing import Any, Iterator, Tuple


Key = str
Value = Any


class Source(abc.ABC):
    @abc.abstractmethod
    def iter(self) -> Iterator[Tuple[Key, Value]]:
        ...
