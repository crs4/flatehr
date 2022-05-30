#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import logging

import pytest

from flatehr.core import Composition, IncompatibleDataType, NotaLeaf, NullFlavour
from flatehr.factory import composition_factory, template_factory
from flatehr.core import flat

logging.basicConfig(level=logging.DEBUG)


@pytest.mark.parametrize("backend", composition_factory.backends())
@pytest.mark.parametrize("web_template_path", ["./tests/resources/web_template.json"])
def test_factory(composition, template):
    assert isinstance(composition, Composition)
    assert composition.template == template
    assert flat(composition) == {}


@pytest.mark.parametrize("backend", template_factory.backends())
@pytest.mark.parametrize("web_template_path", ["./tests/resources/web_template.json"])
def test_composition_add_multiple_instances(composition):
    path = "test/histopathology/result_group/laboratory_test_result/any_event"

    composition[f"{path}/test_name"] = {"": "test-0"}

    assert flat(composition) == {f"{path}:0/test_name": "test-0"}

    composition[f"{path}/test_name"] = {"": "test-0-0"}
    assert flat(composition) == {f"{path}:0/test_name": "test-0-0"}

    composition.add(path)
    composition[f"{path}/test_name"] = {"": "test-1"}

    assert flat(composition) == {
        f"{path}:0/test_name": "test-0-0",
        f"{path}:1/test_name": "test-1",
    }

    composition[f"{path}:0/test_name"] = {"": "test-0-0-0"}
    assert flat(composition) == {
        f"{path}:0/test_name": "test-0-0-0",
        f"{path}:1/test_name": "test-1",
    }


#  @pytest.mark.parametrize("backend", template_factory.backends())
#  def test_composition_create_dv_text_with_default(composition):
#      path = "test/targeted_therapy_start/start_of_targeted_therapy/from_event"
#      node = composition.create_node(path)
#      assert node.value.value == "Primary diagnosis"


@pytest.mark.skip("to be updated")
@pytest.mark.parametrize("backend", template_factory.backends())
@pytest.mark.parametrize("web_template_path", ["./tests/resources/web_template.json"])
def test_composition_set_defaults(composition):
    composition[
        "test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy/"
    ] = {"": "P1W"}

    composition.set_defaults()
    flat_composition = flat(composition)
    assert (
        "test/targeted_therapy_start/start_of_targeted_therapy/from_event"
        in flat_composition
    )


@pytest.mark.skip("to be updated")
@pytest.mark.parametrize("backend", template_factory.backends())
@pytest.mark.parametrize("web_template_path", ["./tests/resources/web_template.json"])
def test_set_null_flavour(composition):
    null_flavour = NullFlavour(value="unknown", code="253", terminology="openehr")
    composition[
        "/test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy/"
    ] = null_flavour._as_dict()
    flat_composition = flat(composition)
    assert (
        flat_composition[
            "test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy/_null_flavour|value"
        ]
        == null_flavour.value
    )
    assert (
        flat_composition[
            "test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy/_null_flavour|code"
        ]
        == null_flavour.code
    )
    assert (
        flat_composition[
            "test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy/_null_flavour|terminology"
        ]
        == null_flavour.terminology
    )
    #  assert (
    #      flat_composition[
    #          "test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy"
    #      ]
    #  == ""
    #  )


#  @pytest.mark.parametrize("backend", template_factory.backends())
#  @pytest.mark.parametrize(
#      "web_template_path", ["./tests/resources/complex_template.json"]
#  )
#  def test_build(composition, xml, xml_mapper, converter):
#      build(composition, xml_mapper, converter)
#      assert flatten(composition) == {
#          "test/context/case_identification/patient_pseudonym": "0000",
#          "test/histopathology/result_group/laboratory_test_result/any_event:0/invasion_front/anatomical_pathology_finding:0/digital_imaging_invasion_front/availability_invasion_front_digital_imaging": "Can be generated",
#          "test/histopathology/result_group/laboratory_test_result/any_event:1/invasion_front/anatomical_pathology_finding:0/digital_imaging_invasion_front/availability_invasion_front_digital_imaging": "Can be generated",
#      }
