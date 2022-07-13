from collections import defaultdict
from typing import (
    Dict,
    Iterator,
    Optional,
    Set,
    Tuple,
)


from flatehr.core import Composition
from flatehr.rm import RMObject, get_model_class
from flatehr.core import Template, TemplatePath
from pipe import Pipe


@Pipe
def remap_to_template_path(
    key_values: Iterator[Tuple[str, str]], mapping: Dict[str, TemplatePath]
) -> Iterator[Tuple[TemplatePath, str]]:
    for key, value in key_values:
        yield (TemplatePath(mapping[key]), value)


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
