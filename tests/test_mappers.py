#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pytest

from flatehr.mappers import XPathMapping
from flatehr.rm import NullFlavour
from flatehr.rm.models import DVText


@pytest.mark.parametrize(
    "mapping",
    [
        {
            "//ns:Event[@eventtype='Sample']": "test/laboratory_test_result/any_event",
            "//ns:Dataelement_54_2/text()": "test/laboratory_test_result/any_event/specimen/material_type/",
        }
    ],
)
def test_xpath_mapper(mapping, xml):
    xpath_mapping = XPathMapping(mapping)
    #  import pudb
    #
    #  pudb.set_trace()
    values = list(xpath_mapping.get_values(xml))
    expected_values = [
        ("test/laboratory_test_result/any_event", None),
        (
            "test/laboratory_test_result/any_event/specimen/material_type/",
            DVText(value="Tumor tissue"),
        ),
        ("test/laboratory_test_result/any_event", None),
        (
            "test/laboratory_test_result/any_event/specimen/material_type/",
            DVText(value="Other"),
        ),
    ]
    assert values == expected_values
