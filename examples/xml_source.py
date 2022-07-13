#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from pipe import map, tee

from flatehr.factory import composition_factory, template_factory
from flatehr.flat import flatten
from flatehr.http import OpenEHRClient
from flatehr.integration.converters import (
    create_rm_objects,
    get_value_from_default,
    get_value_kwargs,
    populate,
    remove_dash,
    xpath_to_template_path,
)
from flatehr.integration.sources import XPathSource

xpath_mapping = {
    "//ns:Dataelement_49_1/text()": "test/lab_result_details/result_group/laboratory_test_result/any_event/test_name",
    "//ns:Identifier/text()": "test/context/report_id",
    "//ns:Location/@name": "test/context/setting",
}
xml_file = open("../tests/resources/test.xml", "r")
client = OpenEHRClient("http://ehr.base", dry_run=True)


xpath_value_map = XPathSource(list(xpath_mapping.keys()), xml_file)


template = template_factory(
    "anytree", json.load(open("../tests/resources/web_template.json", "r"))
).get()
composition = composition_factory("anytree", template).get()


ehr_id = dict(xpath_value_map())["//ns:Identifier/text()"]

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
    xpath_value_map()
    | xpath_to_template_path(xpath_mapping)
    | remove_dash()
    | get_value_kwargs(value_mapping)
    | get_value_from_default(template)
    | create_rm_objects(template)
    | populate(composition)
    | map(lambda c: flatten(c))
    | tee
)
