import abc
import logging
from typing import Generic, Iterator, NewType

from pipe import map

from flatehr.composition import Composition
from flatehr.http import OpenEHRClient
from flatehr.rm import RMObject
from flatehr.integration import K, Message, V
from flatehr.template import TemplatePath


class Destination(abc.ABC, Generic[K, V]):
    @abc.abstractmethod
    def __call__(self, messages: Iterator[Message[K, V]]):
        ...


EhrId = NewType("EhrId", str)
logger = logging.getLogger()


class CompositionEndpoint(Destination[EhrId, Composition]):
    def __init__(self, client: OpenEHRClient) -> None:
        self._client = client

    def __call__(self, messages: Iterator[Message[EhrId, Composition]]):
        for message in messages:
            if message.key and message.value:
                self._client.post_composition(message.value, message.key)
            else:
                logger.debug("skipping message %s", message)
