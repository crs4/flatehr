#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from flatehr.mappers import XPathMapping
from flatehr.rm import NullFlavour
from flatehr.rm.models import DVText


@pytest.mark.parametrize(
    "mapping",
    [
        {
            "//Event[@eventtype='Sample']": "test/laboratory_test_result/any_event",
            "//Dataelement_54_2": "test/laboratory_test_result/any_event/specimen/material_type/",
        }
    ],
)
def test_xpath_mapper(mapping, xml):
    xpath_mapping = XPathMapping(mapping)
    values = list(xpath_mapping.get_values(xml))
    expected_values = [
        ("test/laboratory_test_result/any_event", NullFlavour.get_default()),
        (
            "test/laboratory_test_result/any_event/specimen/material_type/",
            DVText(value="Tumor tissue"),
        ),
        ("test/laboratory_test_result/any_event", NullFlavour.get_default()),
        (
            "test/laboratory_test_result/any_event/specimen/material_type/",
            DVText(value="Other"),
        ),
    ]
    assert values == expected_values
