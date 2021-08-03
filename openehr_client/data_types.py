import abc
import sys
from dataclasses import dataclass
from typing import Dict, Union


def _camel(snake_str):
    "from https://stackoverflow.com/questions/19053707/converting-snake-case-to-lower-camel-case-lowercamelcase"
    words = snake_str.lower().split('_')
    return ''.join([*map(str.title, words)])


def factory(rm_type: str, *args, **kwargs):
    dv_stripped = rm_type.replace('DV_', '', 1)
    class_name = _camel(dv_stripped)
    return getattr(sys.modules[__name__], class_name)(*args, **kwargs)


class DataValue(abc.ABC):
    @abc.abstractmethod
    def to_json(self) -> Union[Dict, str]:
        ...


@dataclass
class Text(DataValue):
    value: str

    def to_json(self) -> str:
        return self.value


@dataclass
class DateTime(Text):
    ...


@dataclass
class CodePhrase(DataValue):
    terminology: str
    code: str
    preferred_term: str = None

    def to_json(self) -> Dict:
        dct = {'code': self.code, 'terminology': self.terminology}
        if self.preferred_term:
            dct['preferred_term'] = self.preferred_term
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

    def to_json(self) -> Dict:
        dct = self._code_phrase.to_json()
        dct['value'] = self.value
        return dct
