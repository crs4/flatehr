import abc
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict


def _camel(snake_str):
    "from https://stackoverflow.com/questions/19053707/converting-snake-case-to-lower-camel-case-lowercamelcase"
    words = snake_str.lower().split("_")
    return "".join([*map(str.title, words)])


@dataclass
class NullFlavour:
    value: str
    code: str
    terminology: str

    @staticmethod
    def get_default():
        return NullFlavour("unknown", "253", "openehr")

    def to_flat(self, path: str) -> Dict:
        flat = {}
        flat[f"{path}/_null_flavour|value"] = self.value
        flat[f"{path}/_null_flavour|code"] = self.code
        flat[f"{path}/_null_flavour|terminology"] = self.terminology

        # workaround for ehrbase expecting value even in case of NullFlavour
        # (at least for some data types)
        flat[path] = "1"
        return flat


class DataValue(abc.ABC):
    @abc.abstractmethod
    def to_flat(self, path: str) -> Dict[str, str]:
        ...


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
        return datetime(year=self.year, month=self.month, day=self.day).isoformat()

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
        dct = {f"{path}|code": self.code, f"{path}|terminology": self.terminology}
        if self.preferred_term:
            dct[f"{path}|preferred_term"] = self.preferred_term
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
        dct[f"{path}|value"] = self.value
        return dct


@dataclass
class Identifier(DataValue):
    id_: str
    issuer: str = None
    assigner: str = None
    type_: str = None

    def to_flat(self, path: str) -> Dict:
        dct = {f"{path}|id": self.id_}
        for attr in ("issuer", "assigner", "type_"):
            value = getattr(self, attr)
            if value is not None:
                dct[f'{path}|{attr.strip("_")}'] = value
        return dct


@dataclass
class PartyProxy(DataValue):
    # TODO: check if it is the right representation
    value: str

    def to_flat(self, path: str) -> Dict:
        return {f"{path}|name": self.value}


@dataclass
class IsmTransition(DataValue):
    current_state: CodedText

    def to_flat(self, path: str) -> Dict:
        return self.current_state.to_flat(os.path.join(path, "current_state"))


class Factory:
    def __init__(self, web_template_node):
        self.web_template_node = web_template_node
        self._class_method_mapping = {}

        for method in dir(self):
            if callable(getattr(self, method)) and method.startswith("_create"):
                class_name = _camel(method.split("_")[-1])
                self._class_method_mapping[class_name] = method

    def create(self, **kwargs) -> DataValue:
        rm_type = self.web_template_node.rm_type
        dv_name = rm_type.replace("DV_", "", 1)

        try:
            create_method = getattr(self, f"_create_{dv_name.lower()}")
        except AttributeError:
            create_method = getattr(sys.modules[__name__], _camel(dv_name))
        try:
            return create_method(
                **kwargs,
            )
        except TypeError as ex:
            raise FactoryWrongArguments(
                f"failed building {rm_type}, {self.web_template_node.path}. \
                Given  kwargs {kwargs}"
            ) from ex

    def _create_text(
        self,
        *,
        value: str = None,
    ) -> Text:
        if value is None:
            value = self.web_template_node.inputs[0]["defaultValue"]
        return Text(value)

    def _create_datetime(
        self,
        *,
        year: int,
        month: int,
        day: int,
    ) -> DateTime:
        return DateTime(year, month, day)

    def _create_coded_text(
        self,
        value: str,
        code: str = None,
        terminology: str = None,
    ) -> CodedText:
        code_info = self.web_template_node.inputs[0]
        if value and not code:
            for el in code_info.get("list", []):
                try:
                    label = el["label"]
                except KeyError:
                    label = el["localizedLabels"]["en"]
                if label.lower() == value.lower():
                    code = el["value"]
                    break
        else:
            code = code or code_info.get("defaultValue")
            for el in code_info.get("list", []):
                if el["value"] == code:
                    value = el["label"]
                    break

        if terminology is None:
            try:
                terminology = code_info["terminology"]
            except KeyError:
                terminology = list(el["termBindings"].values())[0]["value"]
        return CodedText(value=value, code=code, terminology=terminology)

    def _create_ismtransition(
        self,
        current_state_value: str,
        current_state_terminology: str,
        current_state_code: str,
        current_state_preferred_term=None,
    ) -> IsmTransition:

        current_state = CodedText(
            current_state_value,
            current_state_terminology,
            current_state_code,
            current_state_preferred_term,
        )

        return IsmTransition(current_state)


class FactoryWrongArguments(Exception):
    pass
