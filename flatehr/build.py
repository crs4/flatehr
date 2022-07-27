#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dataclasses
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Sequence, TextIO, Tuple

import jq
from dateutil.parser import parse as parse_date
from jinja2 import Environment
from pyaml import yaml

from flatehr.client import BasicAuth, OpenEHRClient
from flatehr.core import Composition, NullFlavour, Template, TemplatePath
from flatehr.factory import composition_factory, template_factory
from flatehr.readers import xpath_value_map


SourceKey = str
Suffix = str
CodeStr = str
Ctx = Dict


def main(input_file: str, template_file: str, conf_file: str):
    conf = yaml.safe_load(open(conf_file, "r"))
    paths = [
        Path(
            k,
            v.get("maps_to", []),
            v.get("suffixes", {}),
            v.get("value_map", {}),
            NullFlavour(**v["null_flavor"]) if "null_flavor" in v else None,
        )
        if isinstance(v, dict)
        else Path(k, [], {"": v})
        for k, v in conf["paths"].items()
    ]

    template_fn = template_factory("anytree", json.load(open(template_file, "r"))).get()
    composition = composition_factory("anytree", template_fn).get()
    composition, ctx = build_composition(
        composition,
        paths,
        open(input_file, "r"),
        conf.get("set_missing_required_to_default", True),
    )
    client = OpenEHRClient(
        "http://localhost:8089", BasicAuth("ehrbase-user", "SuperSecretPassword")
    )
    ehr_id = client.create_ehr()
    print(ehr_id)
    client.post_composition(composition, ehr_id, ctx)


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


def build_composition(
    composition: Composition,
    paths: Sequence[Path],
    input_file: TextIO,
    set_missing_required_to_default: bool = True,
) -> Tuple[Composition, Ctx]:

    inverse_mappings: Dict[SourceKey, List[Path]] = defaultdict(lambda: [])
    pending_value_dicts: Dict[
        Tuple[SourceKey, TemplatePath], List[ValueDict]
    ] = defaultdict(lambda: [])

    ctx = {}
    for path in paths:
        for source in path.maps_to:
            inverse_mappings[source].append(path)

        if not path.maps_to:
            value_dict = ValueDict(
                composition.template, path, path.value_map, path.null_flavor
            )
            if path._id.startswith("ctx/"):
                ctx[path._id] = value_dict
            else:
                composition[path._id] = value_dict

    source_kvs: Iterator[Tuple[SourceKey, Optional[str]]] = xpath_value_map(
        list(inverse_mappings.keys()), input_file
    )

    consumed_paths = []
    for source_key, source_value in source_kvs:
        _paths = inverse_mappings[source_key]
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

    for path in set([p for p in paths if not p._id.startswith("ctx")]) - set(
        consumed_paths
    ):
        if path.null_flavor is not None:
            composition[path._id] = path.null_flavor
        elif not path.maps_to:
            composition[path._id] = {k: v for k, v in path.suffixes.items()}

    if set_missing_required_to_default:
        composition.set_defaults()
    return composition, ctx


def date_isoformat(date: str) -> str:
    return parse_date(date).isoformat()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("-t", dest="template", required=True)
    parser.add_argument("-c", dest="conf", required=True)
    args = parser.parse_args()
    main(args.input, args.template, args.conf)
