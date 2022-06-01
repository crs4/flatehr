#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from flatehr import template_factory
from flatehr.template import Template


@pytest.mark.parametrize("backend", template_factory.backends())
def test_factory(template):
    assert isinstance(template, Template)

    assert template.root._id == "test"
    assert template.root.rm_type == "COMPOSITION"
    assert template.root.aql_path == ""
    assert template.root.required
    assert template.root.inf_cardinality == False
    assert len(template.root.children) == 7

    children = template.root.children
    assert [child._id for child in children] == [
        "context",
        "lab_result_details",
        "category",
        "language",
        "territory",
        "composer",
        "targeted_therapy_start",
    ]
    context = children[0]
    report_id = context.children[0]
    assert report_id._id == "report_id"


@pytest.mark.parametrize("backend", template_factory.backends())
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
                "annotations": {},
                "inputs": None,
            },
        ),
        (
            "test/context/start_time",
            {
                "_id": "start_time",
                "rm_type": "DV_DATE_TIME",
                "required": True,
                "inf_cardinality": False,
                "aql_path": "/context/start_time",
                "annotations": {},
                "inputs": [{"type": "DATETIME"}],
            },
        ),
    ],
)
def test_attrs(template_node, expected_attrs):
    for k, v in expected_attrs.items():
        assert getattr(template_node, k) == v
