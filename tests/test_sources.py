#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from flatehr.integration import xpath_value_map


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
    xpath_source = xpath_value_map([p for p in paths], xml)
    values = tuple(xpath_source)
    assert values == expected_values
