#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from flatehr.sources.json import JsonPathSource

from flatehr.sources.xml import XPathSource


@pytest.mark.parametrize(
    "expected_values",
    [
        (
            ("//ns:Event[@eventtype='Sample']", None),
            ("//ns:Dataelement_54_2/text()", "Tumor tissue"),
            ("//ns:Event[@eventtype='Sample']", None),
            ("//ns:Dataelement_54_2/text()", "Other"),
        )
    ],
)
def test_xpath_source(expected_values, xml_source):
    paths = set([v[0] for v in expected_values])
    xpath_source = XPathSource(xml_source, [p for p in paths])
    values = tuple(xpath_source.iter())
    assert values == expected_values


@pytest.mark.parametrize(
    "expected_values",
    [
        (
            ("$..Event[?(@.@eventtype == Sample)]", None),
            ("$..Dataelement_54_2.'#text'", "Tumor tissue"),
            ("$..Event[?(@.@eventtype == Sample)]", None),
            ("$..Dataelement_54_2.'#text'", "Other"),
        )
    ],
)
def test_jsonpath_source(expected_values, json_source):
    paths = set([v[0] for v in expected_values])
    with open(json_source, "r") as f:
        xpath_source = JsonPathSource(f, [p for p in paths])
    values = tuple(xpath_source.iter())
    assert values == expected_values
