#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from typing import Iterator, Optional, Tuple

from dateutil.parser import parse as parse_date
from pyaml import yaml
from flatehr.build import Config, SourceKey, build_composition

from flatehr.core import flat
from flatehr.factory import template_factory
from flatehr.sources.json import JsonPathSource
from flatehr.sources.xml import XPathSource


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

    conf = conf_from_file(conf_file)
    template = template_factory("anytree", json.load(open(template_file, "r"))).get()
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
            template,
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

    conf = conf_from_file(conf_file)
    template = template_factory("anytree", json.load(open(template_file, "r"))).get()
    jsonpath_source = JsonPathSource(
        open(input_file, "r"), list(conf.inverse_mappings.keys())
    )
    source_kvs: Iterator[Tuple[SourceKey, Optional[str]]] = jsonpath_source.iter()
    composition, ctx, ehr_id = build_composition(
        conf,
        template,
        source_kvs,
    )
    _print_output(composition, ctx, None if skip_ehr_id else ehr_id)


def _print_output(composition, ctx, ehr_id=None):
    flat_comp = json.dumps(flat(composition, ctx))
    if ehr_id:
        print(ehr_id, flat_comp)
    else:
        print(flat_comp)


def skeleton(template_file: str):
    """Generate a configuration skeleton for the given template.

    :param template_file: the path to the web template (json)
    """
    template = template_factory("anytree", json.load(open(template_file, "r"))).get()
    print(template.get_conf_skeleton())


def date_isoformat(date: str) -> str:
    return parse_date(date).isoformat()


def conf_from_file(conf_file: str) -> Config:
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
