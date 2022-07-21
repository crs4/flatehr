#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import json

import pyaml
from pipe import map, tee

from flatehr.factory import composition_factory, template_factory
from flatehr.helpers import (
    create_rm_objects,
    get_value_from_default,
    get_value_kwargs,
    populate,
    remap_to_template_path,
    remove_dash,
    xpath_value_map,
)
from flatehr.http import OpenEHRClient
from flatehr.serializers import flat

xpath_mapping = {
    "//ns:Dataelement_49_1/text()": "test/lab_result_details/result_group/laboratory_test_result/any_event/test_name",
    "//ns:Identifier/text()": "test/context/report_id",
    "//ns:Location/@name": "test/context/setting",
}


def main(input_fn: str, template_fn: str, mapping_fn: str):
    xml_file = open(input_fn, "r")
    mapping = pyaml.yaml.safe_load(open(mapping_fn, "r"))
    #  client = OpenEHRClient("http://ehr.base", dry_run=True)

    template_fn = template_factory("anytree", json.load(open(template_fn, "r"))).get()
    composition = composition_factory("anytree", template_fn).get()

    xpath_values = list(xpath_value_map(tuple(mapping.keys()), xml_file))
    #  ehr_id = dict(xpath_values)["//ns:Identifier/text()"]

    value_mapping = {
        "test/context/setting": {
            "test": {
                "defining_code": {
                    "terminology_id": {"value": "openehr"},
                    "code_string": 238,
                },
                "value": "other",
            }
        }
    }
    list(
        xpath_values
        | tee
        | remap_to_template_path(mapping)
        | remove_dash()
        | get_value_from_default(template_fn)
        | get_value_kwargs(value_mapping)
        | create_rm_objects(template_fn)
        | populate(composition)
        | map(lambda c: flat(c))
        | tee
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="etl compositions")
    parser.add_argument("filename", type=str)
    parser.add_argument(
        "-t",
        dest="template",
    )
    parser.add_argument("-m", dest="mapping")

    args = parser.parse_args()
    main(args.filename, args.template, args.mapping)
