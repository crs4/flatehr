#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

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
def test_xpath_mapper(expected_values, xml):
    paths = set([v[0] for v in expected_values])
    xpath_source = XPathSource(xml, [p for p in paths])
    values = tuple(xpath_source.iter())
    assert values == expected_values
