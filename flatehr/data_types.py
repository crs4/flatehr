import abc
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Union


def _camel(snake_str):
    "from https://stackoverflow.com/questions/19053707/converting-snake-case-to-lower-camel-case-lowercamelcase"
    words = snake_str.lower().split('_')
    return ''.join([*map(str.title, words)])


def factory(web_template_node, *args, **kwargs):
    dv_stripped = web_template_node.rm_type.replace('DV_', '', 1)
    class_name = _camel(dv_stripped)
    try:
        return getattr(sys.modules[__name__],
                       class_name).create(*args, **kwargs)
    except TypeError as ex:
        raise FactoryWrongArguments(
            f'failed building {class_name}, {web_template_node.path}. Given args: {args},\
            kwargs {kwargs}') from ex


class FactoryWrongArguments(Exception):
    pass


class DataValue(abc.ABC):
    @abc.abstractmethod
    def to_flat(self, path: str) -> Dict:
        ...

    @classmethod
    def create(cls, *args, **kwargs) -> "DataValue":
        return cls(*args, **kwargs)


@dataclass
class Text(DataValue):
    value: str

    def to_flat(self, path: str) -> Dict:
        return {path: self.value}


@dataclass
class DateTime(DataValue):
    year: int
    month: int = 1
    day: int = 1

    @property
    def value(self):
        return datetime(year=self.year, month=self.month,
                        day=self.day).isoformat()

    def to_flat(self, path: str) -> Dict:
        return {path: self.value}


@dataclass
class Date(Text):
    ...


@dataclass
class Duration(Text):
    ...


@dataclass
class Boolean(Text):
    ...


@dataclass
class CodePhrase(DataValue):
    terminology: str
    code: str
    preferred_term: str = None

    def to_flat(self, path: str) -> Dict:
        dct = {
            f'{path}|code': self.code,
            f'{path}|terminology': self.terminology
        }
        if self.preferred_term:
            dct[f'{path}|preferred_term'] = self.preferred_term
        return dct


class CodedText(DataValue):
    def __init__(self, value, terminology, code, preferred_term=None):
        self.value = value
        self._code_phrase = CodePhrase(terminology, code, preferred_term)

    @property
    def terminology(self):
        return self._code_phrase.terminology

    @property
    def code(self):
        return self._code_phrase.code

    @property
    def preferred_term(self):
        return self._code_phrase.preferred_term

    def to_flat(self, path: str) -> Dict:
        dct = self._code_phrase.to_flat(path)
        dct[f'{path}|value'] = self.value
        return dct


@dataclass
class Identifier(DataValue):
    id_: str
    issuer: str = None
    assigner: str = None
    type_: str = None

    def to_flat(self, path: str) -> Dict:
        dct = {f'{path}|id': self.id_}
        for attr in ('issuer', 'assigner', 'type_'):
            value = getattr(self, attr)
            if value is not None:
                dct[f'{path}|{attr.strip("_")}'] = value
        return dct


@dataclass
class PartyProxy(DataValue):
    # TODO: check if it is the right representation
    name: str

    def to_flat(self, path: str) -> Dict:
        return {f'{path}|name': self.name}


@dataclass
class IsmTransition(DataValue):
    current_state: CodedText

    @classmethod
    def create(cls,
               current_state_value,
               current_state_terminology,
               current_state_code,
               current_state_preferred_term=None) -> "IsmTransition":
        current_state = CodedText(current_state_value,
                                  current_state_terminology,
                                  current_state_code,
                                  current_state_preferred_term)

        return cls(current_state)

    def to_flat(self, path: str) -> Dict:
        return self.current_state.to_flat(os.path.join(path, 'current_state'))
