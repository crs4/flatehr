import abc
from typing import Generic, List, TypeVar

from flatehr.core import Composition, Template
from flatehr.impl.anytree_core import CompositionFactory, TemplateFactory

T = TypeVar("T", Template, Composition)


class BaseFactory(Generic[T], abc.ABC):
    @abc.abstractmethod
    def get(self) -> T:
        ...


class MetaFactory:
    def __init__(
        self,
    ):
        self._registry = {}

    def __call__(self, backend: str, *args, **kwargs) -> BaseFactory:
        try:
            return self._registry[backend](*args, **kwargs)
        except KeyError as ex:
            raise UnsupportedBackend(backend) from ex

    def register(self, backend, func):
        self._registry[backend] = func

    def backends(
        self,
    ) -> List[str]:
        return list(self._registry.keys())


class UnsupportedBackend(Exception):
    ...


template_factory = MetaFactory()
composition_factory = MetaFactory()

template_factory.register("anytree", TemplateFactory)
composition_factory.register("anytree", CompositionFactory)
