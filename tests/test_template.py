#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from flatehr import template_factory
from flatehr.core import Template


@pytest.mark.parametrize("backend", template_factory.backends())
@pytest.mark.parametrize("web_template_path", ["./tests/resources/web_template.json"])
def test_factory(template):
    assert isinstance(template, Template)

    assert template.root._id == "test"
    assert template.root.rm_type == "COMPOSITION"
    assert template.root.aql_path == ""
    assert template.root.required
    assert template.root.inf_cardinality == False
    assert len(template.root.children) == 4

    children = template.root.children
    assert set([child._id for child in children]) == set(
        [
            "context",
            "histopathology",
            "category",
            "patient_data",
        ]
    )
    context = children[0]
    report_id = context.children[0]
    assert report_id._id == "case_identification"


@pytest.mark.parametrize("backend", template_factory.backends())
@pytest.mark.parametrize("web_template_path", ["./tests/resources/web_template.json"])
@pytest.mark.parametrize(
    "path,expected_attrs",
    [
        (
            "test/context",
            {
                "_id": "context",
                "rm_type": "EVENT_CONTEXT",
                "required": True,
                "inf_cardinality": False,
                "aql_path": "/context",
                "annotations": (),
                "inputs": (),
            },
        ),
    ],
)
def test_attrs(template_node, expected_attrs):
    for k, v in expected_attrs.items():
        assert getattr(template_node, k) == v
