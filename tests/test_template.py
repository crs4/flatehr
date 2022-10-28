#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from flatehr.factory import template_factory
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


@pytest.mark.parametrize("backend", template_factory.backends())
@pytest.mark.parametrize("web_template_path", ["./tests/resources/web_template.json"])
@pytest.mark.parametrize(
    "expected_conf_skeleton",
    [
        """paths:
  ctx/category: #  required
    maps_to: []
    suffixes:
      "|code": ""
  ctx/encoding: #  required
    maps_to: []
  ctx/language: #  required
    maps_to: []
  ctx/subject: #  required
    maps_to: []
    suffixes:
      "|id": ""
      "|id_scheme": ""
      "|id_namespace": ""
      "|name": ""
  ctx/time: #  required
    maps_to: []
  test/context/case_identification/participation_in_clinical_study: # NOT required
    maps_to: []
  test/context/case_identification/patient_pseudonym: #  required
    maps_to: []
  test/histopathology/result_group/laboratory_test_result/any_event/test_name: #  required
    maps_to: []
  test/patient_data/gender/biological_sex: #  required
    maps_to: []
    suffixes:
      "|code": ""
  test/patient_data/metastasis_diagnosis/metastasis_diagnosis2/metastasis_diagnosis/from_event: #  required
    maps_to: []
  test/patient_data/metastasis_diagnosis/metastasis_diagnosis2/metastasis_diagnosis/time_of_recurrence: #  required
    maps_to: []
    suffixes:
      "|week": ""
  test/patient_data/metastasis_diagnosis/metastasis_diagnosis: #  required
    maps_to: []
    suffixes:
      "|code": ""
  test/patient_data/primary_diagnosis/date_of_diagnosis: # NOT required
    maps_to: []
  test/patient_data/primary_diagnosis/diagnosis_timing/primary_diagnosis/age_at_diagnosis: #  required
    maps_to: []
    suffixes:
      "|year": ""
  test/patient_data/primary_diagnosis/primary_diagnosis: #  required
    maps_to: []
    suffixes:
      "|code": ""
"""
    ],
)
def test_conf_skeleton(template, expected_conf_skeleton):
    conf_skeleton = template.get_conf_skeleton()
    assert conf_skeleton == expected_conf_skeleton
