import abc
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Union


def _camel(snake_str):
    "from https://stackoverflow.com/questions/19053707/converting-snake-case-to-lower-camel-case-lowercamelcase"
    words = snake_str.lower().split("_")
    return "".join([*map(str.title, words)])


@dataclass
class NullFlavour:
    # place_holder is a workaround for ehrbase expecting value even in case of NullFlavour
    # (at least for some data types)
    value: str
    code: str
    terminology: str
    place_holder: str = ""

    @staticmethod
    def get_default(place_holder=""):
        return NullFlavour("unknown", "253", "openehr", place_holder)

    def to_flat(self, path: str) -> Dict:
        flat = {}
        flat[f"{path}/_null_flavour|value"] = self.value
        flat[f"{path}/_null_flavour|code"] = self.code
        flat[f"{path}/_null_flavour|terminology"] = self.terminology

        flat[path] = self.place_holder
        return flat


class DATA_VALUE(abc.ABC):
    @abc.abstractmethod
    def to_flat(self, path: str) -> Dict[str, str]:
        ...


@dataclass
class DV_TEXT(DATA_VALUE):
    value: Union[str, NullFlavour]

    def to_flat(self, path: str) -> Dict:
        return {path: self.value}


@dataclass
class DV_DATE_TIME(DATA_VALUE):
    year: int
    month: int = 1
    day: int = 1

    @property
    def value(self):
        return datetime(year=self.year, month=self.month, day=self.day).isoformat()

    def to_flat(self, path: str) -> Dict:
        return {path: self.value}


@dataclass
class DV_DATE(DV_TEXT):
    ...


@dataclass
class DV_DURATION(DV_TEXT):
    def __post_init__(self):
        if not self.value:
            self.value = NullFlavour.get_default("P1W")


@dataclass
class DVBoolean(DV_TEXT):
    ...


@dataclass
class CODE_PHRASE(DATA_VALUE):
    terminology: str
    code: str
    preferred_term: Optional[str] = None

    def to_flat(self, path: str) -> Dict:
        dct = {f"{path}|code": self.code, f"{path}|terminology": self.terminology}
        if self.preferred_term:
            dct[f"{path}|preferred_term"] = self.preferred_term
        return dct


class DV_CODED_TEXT(DATA_VALUE):
    def __init__(self, value, terminology, code, preferred_term=None):
        self.value = value
        self._code_phrase = CODE_PHRASE(terminology, code, preferred_term)

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
class DV_IDENTIFIER(DATA_VALUE):
    id_: str
    issuer: Optional[str] = None
    assigner: Optional[str] = None
    type_: Optional[str] = None

    def to_flat(self, path: str) -> Dict:
        dct = {f"{path}|id": self.id_}
        for attr in ("issuer", "assigner", "type_"):
            value = getattr(self, attr)
            if value is not None:
                dct[f'{path}|{attr.strip("_")}'] = value
        return dct


@dataclass
class PARTY_PROXY(DATA_VALUE):
    # TODO: check if it is the right representation
    value: str

    def to_flat(self, path: str) -> Dict:
        return {f"{path}|name": self.value}


@dataclass
class ISM_TRANSITION(DATA_VALUE):
    current_state: DV_CODED_TEXT

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

    def create(self, **kwargs) -> DATA_VALUE:
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
    ) -> DV_TEXT:
        if value is None:
            try:
                value = self.web_template_node.inputs[0]["defaultValue"]
            except (IndexError, KeyError):
                return NullFlavour.get_default()
        return DV_TEXT(value)

    def _create_duration(self, value: str = None):
        if not value:
            return NullFlavour.get_default("P1W")
        return DV_DURATION(value)

    def _create_date_time(
        self,
        year: int = None,
        month: int = 1,
        day: int = 1,
    ) -> DV_DATE_TIME:
        year = year or 9999
        return DV_DATE_TIME(year, month, day)

    def _create_coded_text(
        self,
        value: str = None,
        code: str = None,
        terminology: str = None,
    ) -> DV_CODED_TEXT:
        if value == None and code == None and terminology == None:
            return NullFlavour.get_default()
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
        return DV_CODED_TEXT(value=value, code=code, terminology=terminology)

    def _create_ismtransition(
        self,
        current_state_value: str,
        current_state_terminology: str,
        current_state_code: str,
        current_state_preferred_term=None,
    ) -> ISM_TRANSITION:

        current_state = DV_CODED_TEXT(
            current_state_value,
            current_state_terminology,
            current_state_code,
            current_state_preferred_term,
        )

        return ISM_TRANSITION(current_state)

    def _create_identifier(self, **kwargs):
        if len(kwargs):
            return DV_IDENTIFIER(**kwargs)
        return NullFlavour.get_default()


class FactoryWrongArguments(Exception):
    pass
