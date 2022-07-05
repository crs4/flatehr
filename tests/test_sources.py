#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from flatehr.factory import template_factory

from flatehr.sources import XPathSource


@pytest.mark.parametrize(
    "mapping",
    [
        {
            "//ns:Event[@eventtype='Sample']": "test/lab_result_details/result_group/laboratory_test_result/any_event",
            "//ns:Dataelement_54_2/text()": "test/lab_result_details/result_group/laboratory_test_result/any_event/test_name",
        }
    ],
)
@pytest.mark.parametrize("backend", template_factory.backends())
@pytest.mark.parametrize("web_template_path", ["./tests/resources/web_template.json"])
def test_xpath_mapper(template, mapping, xml):
    xpath_mapping = XPathSource(template, mapping, xml)
    values = list(xpath_mapping.iter())
    expected_values = [
        (
            template[
                "test/lab_result_details/result_group/laboratory_test_result/any_event"
            ],
            None,
        ),
        (
            template[
                "test/lab_result_details/result_group/laboratory_test_result/any_event/test_name"
            ],
            "Tumor tissue",
        ),
        (
            template[
                "test/lab_result_details/result_group/laboratory_test_result/any_event"
            ],
            None,
        ),
        (
            template[
                "test/lab_result_details/result_group/laboratory_test_result/any_event/test_name"
            ],
            "Other",
        ),
    ]
    assert values == expected_values
