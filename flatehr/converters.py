import abc
from typing import Dict, Iterator

from flatehr.composition import Composition
from flatehr.sources import Key, Message
from flatehr.template import Template, TemplateNode, TemplatePath
from pipe import map


class Converter(abc.ABC):
    @abc.abstractmethod
    def convert(
        self, mapping_iterator: Iterator[Message], composition: Composition
    ) -> Composition:
        ...


class BasicConverter(Converter):
    def __init__(self, mapping: Dict[Key, TemplatePath]):
        self._mapping = mapping

    def convert(
        self, mapping_iterator: Iterator[Message], composition: Composition
    ) -> Composition:
        def populate_composition(composition, path, value):
            if value:
                composition[path] = value
            else:
                composition.add(path)

        list(
            mapping_iterator
            | map(lambda message: (self._mapping[message.key], message.value))
            | map(lambda path_value: populate_composition(composition, *path_value))
        )
        return composition


class ValueConverter(Converter):
    def __init__(self, mappings: Dict[str, str], passthrough: bool = False):
        self._mappings = mappings
        self._passthrough = passthrough

    def convert(self, template_node: TemplateNode, value: Value) -> Value:
        try:
            return Value(self._mappings[template_node._id])
        except KeyError as ex:
            if self._passthrough:
                return value
            raise ConversionFailed(f"{type(self)} failed with value {value}") from ex


class DashValueConverter(Converter):
    def __init__(self, *node_ids: str):
        self._node_ids = node_ids

    def convert(self, template_node: TemplateNode, value: Value) -> Value:
        if template_node._id in self._node_ids:
            try:
                return Value(value.split("-", 1)[1].strip())
            except IndexError:
                return value
        raise ConversionFailed(f"{type(self)} cannot map value {value}")


class InputBasedConverter(Converter):
    def convert(self, template_node: TemplateNode, value: Value) -> Value:
        if not template_node.inputs or "list" not in template_node.inputs[0]:
            raise ConversionFailed(f"{type(self)} cannot map value {value}")
        value_from_inputs = None
        value_list = template_node.inputs[0]["list"]
        for item in value_list:
            label = item["label"].lower()
            value_lower = value.lower()
            if label == value_lower:
                value_from_inputs = item["value"]
                break
        if value_from_inputs is None:
            raise RuntimeError(f"invalid value {value} for node {template_node}")
        return Value(value_from_inputs)


class MultiConverter(Converter):
    def __init__(self, *mappers: Converter):
        self._mappers = mappers

    def convert(self, template_node: TemplateNode, value: Value) -> Value:
        for mapper in self._mappers:
            try:
                value = mapper.convert(template_node, value)
                #  break
            except ConversionFailed:
                ...
        return value


class ConversionFailed(Exception):
    ...
