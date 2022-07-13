from collections import defaultdict
from typing import (
    Dict,
    Iterator,
    Optional,
    Set,
    Tuple,
)


from flatehr.core import Composition
from flatehr.integration.sources import XPath
from flatehr.rm import RMObject, get_model_class
from flatehr.core import Template, TemplatePath
from pipe import Pipe

from flatehr.rm.models import DVText


@Pipe
def xpath_to_template_path(
    xpath_values: Iterator[Tuple[XPath, str]], mapping: Dict[XPath, TemplatePath]
) -> Iterator[Tuple[TemplatePath, str]]:
    for xpath, value in xpath_values:
        template_path = TemplatePath(mapping[xpath])
        yield (template_path, value)


@Pipe
def populate(
    path_values: Iterator[Tuple[TemplatePath, RMObject]], composition: Composition
) -> Iterator[Composition]:
    for path_value in list(path_values):
        path, value = path_value
        if value:
            composition[path] = value
        else:
            composition.add(path)

    yield composition


@Pipe
def remove_dash(
    template_paths: Iterator[Tuple[TemplatePath, str]],
    _filter: Optional[Set[TemplatePath]] = None,
) -> Iterator[Tuple[TemplatePath, str]]:
    def _remove_dash(value: str):
        try:
            return value.split("-", 1)[1].strip()
        except IndexError:
            return value

    for tpath, value in template_paths:
        process: bool = True if _filter is None else (tpath in _filter)
        if process:
            yield (tpath, _remove_dash(value))


@Pipe
def get_value_from_default(
    template_paths: Iterator[Tuple[TemplatePath, str]],
    template: Template,
) -> Iterator[Tuple[TemplatePath, str]]:
    for tpath, value in template_paths:
        if value:
            template_node = template[tpath]
            if not template_node.inputs or "list" not in template_node.inputs[0]:
                yield (tpath, value)
                continue
            value_from_inputs = None
            value_list = template_node.inputs[0]["list"]
            for item in value_list:
                label = item["label"].lower()
                value_lower = value.lower()
                if label == value_lower:
                    value_from_inputs = item["value"]
                    break
            if value_from_inputs is None:
                yield (tpath, value)
            else:
                yield tpath, value_from_inputs


@Pipe
def get_value_kwargs(
    tpath_map: Iterator[Tuple[TemplatePath, str]],
    mapping: Optional[Dict[TemplatePath, Dict[str, Dict]]] = None,
) -> Iterator[Tuple[TemplatePath, Dict]]:
    _mapping = defaultdict(lambda: {})
    if mapping:
        _mapping.update(mapping)
    for tpath, value in tpath_map:
        yield tpath, _mapping[tpath].get(value, {"value": value})


@Pipe
def create_rm_objects(
    template_paths: Iterator[Tuple[TemplatePath, Dict]],
    template: Template,
) -> Iterator[Tuple[TemplatePath, RMObject]]:

    for tpath, value in template_paths:
        if value:
            template_node = template[tpath]
            rm_class = get_model_class(template_node.rm_type)
            yield tpath, rm_class(**value)


#  class ValueConverter(Converter):
#      def __init__(self, mappings: Dict[str, str], passthrough: bool = False):
#          self._mappings = mappings
#          self._passthrough = passthrough
#
#      def convert(self, template_node: TemplateNode, value: Value) -> Value:
#          try:
#              return Value(self._mappings[template_node._id])
#          except KeyError as ex:
#              if self._passthrough:
#                  return value
#              raise ConversionFailed(f"{type(self)} failed with value {value}") from ex
#
#

#  class InputBasedConverter(Converter):
#      def convert(self, template_node: TemplateNode, value: Value) -> Value:
#          if not template_node.inputs or "list" not in template_node.inputs[0]:
#              raise ConversionFailed(f"{type(self)} cannot map value {value}")
#          value_from_inputs = None
#          value_list = template_node.inputs[0]["list"]
#          for item in value_list:
#              label = item["label"].lower()
#              value_lower = value.lower()
#              if label == value_lower:
#                  value_from_inputs = item["value"]
#                  break
#          if value_from_inputs is None:
#              raise RuntimeError(f"invalid value {value} for node {template_node}")
#          return Value(value_from_inputs)
#
#
#  class MultiConverter(Converter):
#      def __init__(self, *mappers: Converter):
#          self._mappers = mappers
#
#      def convert(self, template_node: TemplateNode, value: Value) -> Value:
#          for mapper in self._mappers:
#              try:
#                  value = mapper.convert(template_node, value)
#                  #  break
#              except ConversionFailed:
#                  ...
#          return value
#
#
#  class ConversionFailed(Exception):
#      ...
