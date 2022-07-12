#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from pipe import tee

from flatehr.factory import composition_factory, template_factory
from flatehr.http import OpenEHRClient
from flatehr.integration.converters import (
    get_value_from_default,
    populate,
    remove_dash,
    xpath_to_template_path,
)
from flatehr.integration.sources import XPath, XPathSource
from flatehr.template import TemplatePath
from pipe import filter

xpath_mapping = {
    XPath("//ns:Dataelement_49_1/text()"): TemplatePath(""),
    XPath("//ns:Identifier/text()"): TemplatePath("test/context/report_id"),
}
xml_file = open("../tests/resources/test.xml", "r")
client = OpenEHRClient("http://ehr.base", dry_run=True)


xpath_value_map = XPathSource(list(xpath_mapping.keys()), xml_file)


template = template_factory(
    "anytree", json.load(open("../tests/resources/web_template.json", "r"))
).get()
composition = composition_factory("anytree", template).get()
to_composition = populate(composition)


ehr_id = dict(xpath_value_map())["//ns:Identifier/text()"]

list(
    xpath_value_map()
    | xpath_to_template_path(xpath_mapping)
    | remove_dash()
    | get_value_from_default(template)
    | to_composition()
    | tee
)
