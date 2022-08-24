#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dataclasses
import json
from collections import defaultdict
from dataclasses import dataclass
import os
from typing import Dict, Iterator, List, Optional, Sequence, Set, Tuple
from uuid import uuid4

import jq
from dateutil.parser import parse as parse_date
from jinja2 import Environment
from pyaml import yaml

from flatehr.core import Composition, NullFlavour, Template, TemplatePath, flat
from flatehr.factory import composition_factory, template_factory
from flatehr.sources.json import JsonPathSource
from flatehr.sources.xml import XPathSource

SourceKey = str
Suffix = str
CodeStr = str
Ctx = Dict


class Config:
    def __init__(
        self,
        paths: Dict,
        ehr_id: Dict,
        set_missing_required_to_default: bool = True,
    ):
        self._ehr_id = EhrId(set(ehr_id.get("maps_to", [])), ehr_id["value"])
        self._set_missing_required_to_default = set_missing_required_to_default
        self._paths = [
            Path(
                k,
                v.get("maps_to", []),
                v.get("suffixes", {}),
                v.get("value_map", {}),
                NullFlavour(**v["null_flavor"]) if "null_flavor" in v else None,
            )
            if isinstance(v, dict)
            else Path(k, [], {"": v})
            for k, v in paths.items()
        ]
        self._inverse_mappings: Dict[SourceKey, List[Path]] = defaultdict(lambda: [])
        for path in self._paths:
            for map_to in path.maps_to:
                self._inverse_mappings[map_to].append(path)

    @property
    def inverse_mappings(self):
        return self._inverse_mappings

    @property
    def paths(self):
        return self._paths

    @property
    def set_missing_required_to_default(self) -> bool:
        return self._set_missing_required_to_default

    @property
    def ehr_id(self) -> "EhrId":
        return self._ehr_id


@dataclass
class EhrId:
    maps_to: Set[SourceKey]
    value: CodeStr


@dataclass
class Path:
    _id: TemplatePath
    maps_to: Sequence[SourceKey]
    suffixes: Dict[Suffix, CodeStr] = dataclasses.field(default_factory=lambda: {})
    value_map: Dict = dataclasses.field(default_factory=lambda: {})
    null_flavor: Optional[NullFlavour] = None

    def __hash__(self) -> int:
        return hash(self._id)


@dataclass
class ValueDict(dict):
    template: Template
    path: Path
    value_map: Dict[str, Dict[str, str]] = dataclasses.field(default_factory=dict)
    null_flavor: Optional[NullFlavour] = None

    def __post_init__(self):
        self._dict: Dict[str, str] = {}
        self._source_key_value: Dict[SourceKey, str] = {}
        self._populate_dict()

    def completed(self) -> bool:
        return set(self._source_key_value.keys()) == set(self.path.maps_to)

    def add_source_key_value(self, source_key: SourceKey, value: str):
        self._source_key_value[source_key] = value
        if self.completed():
            self._populate_dict()

    def __getitem__(self, key):
        if not self.completed():
            if self.null_flavor:
                return self.null_flavor[key]
            raise ValuesNotReady()

        return self._dict[key]

    def __setitem__(self, k, v):
        raise NotImplementedError()

    def keys(self):
        if not self.completed():
            if self.null_flavor:
                return self.null_flavor.keys()
            raise ValuesNotReady()
        return self._dict.keys()

    def values(self):
        if not self.completed():
            if self.null_flavor:
                return self.null_flavor.values()
            raise ValuesNotReady()
        return self._dict.values()

    def items(self):
        if not self.completed():
            if self.null_flavor:
                return self.null_flavor.items()
            raise ValuesNotReady()
        return self._dict.items()

    def _populate_dict(self):
        if not self.completed():
            return
        maps_to = [
            self._source_key_value[source_key] for source_key in self.path.maps_to
        ]

        for k, v in self.path.suffixes.items():
            if isinstance(v, str):
                v = {"value": v, "jq": False}
            env = Environment()
            env.globals["date_isoformat"] = date_isoformat
            t = env.from_string(v["value"])
            value = t.render(maps_to=maps_to, value_map=self.value_map)
            if v["jq"]:
                tpl = self.template[self.path._id].json()
                value = jq.first(value, tpl)
            self._dict[k] = value


class ValuesNotReady(Exception):
    ...


def from_file(
    input_file: str,
    *,
    template_file: str,
    conf_file: str,
    relative_root: Optional[str] = None,
    skip_ehr_id: bool = False,
):
    """
    Generates composition(s) from a file. xml and json sources supported.
    Prints on stdout an external ehr id (if flag --skip-ehr-id is not set) and the flat composition.
    If --relative-root is set, as many compositions are generated as keys with the given value exists in the source.

    :param input_file: source file
    :param template_file: web template path
    :param conf_file: yaml configuration path
    :param relative_root: id for the root(s) that maps 1:1 to composition
    :param skip_ehr_id: if set, ehr_id is not printed
    """
    handlers = {".xml": from_xml, ".json": from_json}
    ext = os.path.splitext(input_file)[1]
    try:
        handler = handlers[ext]
    except KeyError:
        raise RuntimeError(
            f"file {input_file} not supported, Supported types: {list(handlers.keys())}"
        )
    return handler(
        input_file,
        template_file=template_file,
        conf_file=conf_file,
        relative_root=relative_root,
        skip_ehr_id=skip_ehr_id,
    )


def from_xml(
    input_file: str,
    *,
    template_file: str,
    conf_file: str,
    relative_root: Optional[str] = None,
    skip_ehr_id: bool = False,
):

    conf = _get_conf(conf_file)
    xpath_source = XPathSource(
        open(input_file, "r"), list(conf.inverse_mappings.keys())
    )
    relative_root_elements = (
        xpath_source.get_elements(f"//ns:{relative_root}")
        if relative_root
        else [xpath_source.root]
    )
    for el in relative_root_elements:
        xpath_source.relative_root = el

        source_kvs: Iterator[Tuple[SourceKey, Optional[str]]] = xpath_source.iter()
        composition, ctx, ehr_id = build_composition(
            conf,
            template_file,
            source_kvs,
        )
        _print_output(composition, ctx, None if skip_ehr_id else ehr_id)


def from_json(
    input_file: str,
    *,
    template_file: str,
    conf_file: str,
    relative_root: Optional[str] = None,
    skip_ehr_id: bool = False,
):

    conf = _get_conf(conf_file)
    jsonpath_source = JsonPathSource(
        open(input_file, "r"), list(conf.inverse_mappings.keys())
    )
    source_kvs: Iterator[Tuple[SourceKey, Optional[str]]] = jsonpath_source.iter()
    composition, ctx, ehr_id = build_composition(
        conf,
        template_file,
        source_kvs,
    )
    _print_output(composition, ctx, None if skip_ehr_id else ehr_id)


def _print_output(composition, ctx, ehr_id=None):
    flat_comp = json.dumps(flat(composition, ctx))
    if ehr_id:
        print(ehr_id, flat_comp)
    else:
        print(flat_comp)


def build_composition(
    conf: Config,
    template_file: str,
    source_kvs: Iterator[Tuple[SourceKey, Optional[str]]],
) -> Tuple[Composition, Ctx, str]:

    template = template_factory("anytree", json.load(open(template_file, "r"))).get()
    composition = composition_factory("anytree", template).get()

    pending_value_dicts: Dict[
        Tuple[SourceKey, TemplatePath], List[ValueDict]
    ] = defaultdict(lambda: [])

    ctx = {}
    for path in conf.paths:
        if not path.maps_to:
            value_dict = ValueDict(
                composition.template, path, path.value_map, path.null_flavor
            )
            if path._id.startswith("ctx/"):
                ctx[path._id] = value_dict
            else:
                composition[path._id] = value_dict

    consumed_paths = []
    ehr_id_kvs = {}
    for source_key, source_value in source_kvs:

        if source_key in conf.ehr_id.maps_to:
            ehr_id_kvs[source_key] = source_value

        _paths = conf.inverse_mappings[source_key]
        for path in _paths:
            if "*" in path._id:
                continue

            if not path.suffixes:
                composition.add(path._id)
            else:
                try:
                    value_dicts = pending_value_dicts.pop((source_key, path._id))
                except KeyError:
                    value_dicts = [
                        ValueDict(composition.template, path, path.value_map)
                    ]

                    for k in path.maps_to:
                        if k != source_key:
                            pending_value_dicts[(k, path._id)] += value_dicts

                    if path._id.startswith("ctx/"):
                        ctx[path._id] = value_dicts[0]
                    else:
                        composition[path._id] = value_dicts[0]

                for vd in value_dicts:
                    if source_value:
                        vd.add_source_key_value(source_key, source_value)
            consumed_paths.append(path)

    for path in set([p for p in conf.paths if not p._id.startswith("ctx")]) - set(
        consumed_paths
    ):
        if path.null_flavor is not None:
            composition[path._id] = path.null_flavor
        elif not path.maps_to:
            composition[path._id] = {k: v for k, v in path.suffixes.items()}

    if conf.set_missing_required_to_default:
        composition.set_defaults()

    env = Environment()
    env.globals["random_ehr_id"] = uuid4
    t = env.from_string(conf._ehr_id.value)
    ehr_id = t.render(maps_to=conf.ehr_id.maps_to)
    return composition, ctx, ehr_id


def date_isoformat(date: str) -> str:
    return parse_date(date).isoformat()


def _get_conf(conf_file: str) -> Config:
    conf_kwargs = yaml.safe_load(open(conf_file, "r"))
    return Config(
        paths=conf_kwargs["paths"],
        ehr_id=conf_kwargs["ehr_id"],
        set_missing_required_to_default=conf_kwargs.get(
            "set_missing_required_to_default", True
        ),
    )


if __name__ == "__main__":
    import defopt

    defopt.run([from_file])