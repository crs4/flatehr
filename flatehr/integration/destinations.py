import abc
from typing import Generic, Iterator

from pipe import map

from flatehr.composition import Composition
from flatehr.rm import RMObject
from flatehr.integration import K, Message, V
from flatehr.template import TemplatePath


class Destination(abc.ABC, Generic[K, V]):
    @abc.abstractmethod
    def process(self, messages: Iterator[Message[K, V]]):
        ...


class CompositionEndpoint(Destination[TemplatePath, RMObject]):
    def __init__(self, composition: Composition):
        self._composition = composition

    def convert(self, messages: Iterator[Message[TemplatePath, RMObject]]):
        def populate_composition(composition, path, value):
            if value:
                composition[path] = value
            else:
                composition.add(path)

        list(
            messages
            | map(
                lambda message: populate_composition(
                    self._composition, message.key, message.value
                )
            )
        )
