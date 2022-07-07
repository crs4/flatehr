#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from pipe import tee

from flatehr.factory import composition_factory, template_factory
from flatehr.http import OpenEHRClient
from flatehr.integration.converters import populate, remove_dash, xpath_to_template_path
from flatehr.integration.sources import XPath, XPathSource
from flatehr.template import TemplatePath
from pipe import filter

xpath_mapping = {
    XPath("//ns:Dataelement_54_2/text()"): TemplatePath(""),
    XPath("//ns:Identifier/text()"): TemplatePath(""),
}
xml_file = open("../tests/resources/test.xml", "r")
client = OpenEHRClient("http://ehr.base", dry_run=True)


xpaths = XPathSource(list(xpath_mapping.keys()), xml_file)
to_template_path = xpath_to_template_path(xpath_mapping)


template = template_factory(
    "anytree", json.load(open("../tests/resources/web_template.json", "r"))
).get()
composition = composition_factory("anytree", template).get()
to_composition = populate(composition)


ehr_id = dict(xpaths())["//ns:Identifier/text()"]

list(xpaths() | to_template_path() | remove_dash | to_composition() | tee)
