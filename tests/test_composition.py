#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import logging

import pytest
from flatehr import rm

import flatehr.data_types as data_types
from flatehr.composition import Composition, IncompatibleDataType, NotaLeaf
from flatehr.factory import composition_factory, template_factory
from flatehr.flat import flatten
from flatehr.rm import models
from flatehr.rm.factory import factory
from flatehr.rm.models import CodePhrase

logging.basicConfig(level=logging.DEBUG)


@pytest.mark.parametrize("backend", composition_factory.backends())
def test_factory(composition, template):
    assert isinstance(composition, Composition)
    assert composition.template == template
    assert flatten(composition) == {}


@pytest.mark.parametrize("backend", template_factory.backends())
def test_create_dv_text(composition):
    text = "ok"
    path = "test/context/status"
    composition[path] = rm.DVText(value=text)

    flat = flatten(composition)
    assert flat == {path: text}


@pytest.mark.parametrize("backend", template_factory.backends())
def test_not_a_leaf(composition):
    text = "ok"
    path = "test/context"
    with pytest.raises(NotaLeaf):
        composition[path] = ""


@pytest.mark.skip("TBF")
@pytest.mark.parametrize("backend", template_factory.backends())
def test_incompatible_data_type(composition):
    path = "test/context/status"
    with pytest.raises(IncompatibleDataType):
        composition[path] = ""


@pytest.mark.parametrize("backend", template_factory.backends())
def test_composition_add_multiple_instances(composition):
    path = "test/lab_result_details/result_group/laboratory_test_result/any_event"

    composition[f"{path}/test_name"] = rm.DVText(value="test-0")

    assert flatten(composition) == {f"{path}:0/test_name": "test-0"}

    composition[f"{path}/test_name"] = rm.DVText(value="test-0-0")
    assert flatten(composition) == {f"{path}:0/test_name": "test-0-0"}

    composition.add(path)
    composition[f"{path}/test_name"] = rm.DVText(value="test-1")

    assert flatten(composition) == {
        f"{path}:0/test_name": "test-0-0",
        f"{path}:1/test_name": "test-1",
    }

    composition[f"{path}:0/test_name"] = rm.DVText(value="test-0-0-0")
    assert flatten(composition) == {
        f"{path}:0/test_name": "test-0-0-0",
        f"{path}:1/test_name": "test-1",
    }


#  @pytest.mark.parametrize("backend", template_factory.backends())
#  def test_composition_create_dv_text_with_default(composition):
#      path = "test/targeted_therapy_start/start_of_targeted_therapy/from_event"
#      node = composition.create_node(path)
#      assert node.value.value == "Primary diagnosis"


@pytest.mark.parametrize("backend", template_factory.backends())
def test_composition_create_code_phrase(composition):
    terminology = "ISO_639-1"
    code = "en"
    path = "test/language"

    composition[path] = rm.CodePhrase(
        code_string=code, terminology_id={"value": terminology}
    )
    value = composition[path]
    assert isinstance(value, CodePhrase)
    assert value.terminology_id.value == terminology
    assert value.code_string == code

    flat = flatten(composition)
    assert flat == {
        f"{path}|code": code,
        f"{path}|terminology": terminology,
    }


@pytest.mark.parametrize("backend", template_factory.backends())
def test_composition_create_dv_coded_text(composition):
    text = "ok"
    terminology = "ISO_639-1"
    code = "en"
    path = "test/context/setting"
    composition[path] = rm.DVCodedText(
        value=text,
        defining_code={"code_string": code, "terminology_id": {"value": terminology}},
    )
    dv_coded_text = composition[path]
    assert isinstance(dv_coded_text, rm.DVCodedText)

    assert dv_coded_text.value == text
    assert dv_coded_text.defining_code.code_string == code
    assert dv_coded_text.defining_code.terminology_id.value == terminology

    flat = flatten(composition)
    assert flat == {
        f"{path}|code": code,
        f"{path}|terminology": terminology,
        f"{path}|value": text,
    }


@pytest.mark.parametrize("backend", template_factory.backends())
def test_composition_create_dv_datetime(composition):
    path = "test/context/start_time"
    value = datetime(year=2021, month=4, day=22).isoformat()
    composition[path] = rm.DVDateTime(value=value)
    dt = composition[path]
    assert isinstance(dt, rm.DVDateTime)

    flat = flatten(composition)
    assert flat == {f"{path}": dt.value}


@pytest.mark.parametrize("backend", template_factory.backends())
def test_composition_create_party_identified(composition):
    name = "composer"
    path = "test/composer"
    composition[path] = rm.PartyIdentified(name=name)
    party_identified = composition[path]
    assert isinstance(party_identified, rm.PartyIdentified)
    assert party_identified.name == name

    flat = flatten(composition)
    assert flat == {f"{path}|name": name}


@pytest.mark.parametrize("backend", template_factory.backends())
def test_composition_to_flat(composition):
    text = "ok"
    path_status = "test/context/status"
    composition[path_status] = rm.DVText(value=text)

    terminology = "ISO_639-1"
    code = "en"
    path_lang = "test/language"

    composition[path_lang] = rm.CodePhrase(
        terminology_id={"value": terminology}, code_string=code
    )

    flat = flatten(composition)
    assert flat == {
        f"{path_status}": text,
        f"{path_lang}|code": code,
        f"{path_lang}|terminology": terminology,
    }


@pytest.mark.parametrize("backend", template_factory.backends())
def test_composition_set_all(composition):
    terminology = "ISO_639-1"
    code = "en"
    composition["**/language"] = rm.CodePhrase(
        terminology_id={"value": terminology}, code_string=code
    )

    path_lang = "test/language"

    flat = flatten(composition)
    assert flat == {f"{path_lang}|code": code, f"{path_lang}|terminology": terminology}

    path_lab_test_result = (
        "test/lab_result_details/result_group/laboratory_test_result/any_event"
    )

    for _ in range(2):
        composition.add(path_lab_test_result)

    composition["**/test_name"] = rm.DVText(value="test_name")
    assert flatten(composition) == {
        f"{path_lang}|code": code,
        f"{path_lang}|terminology": terminology,
        f"{path_lab_test_result}:0/test_name": "test_name",
        f"{path_lab_test_result}:1/test_name": "test_name",
    }


@pytest.mark.parametrize("backend", template_factory.backends())
def test_composition_set_defaults(composition):
    composition[
        "test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy/"
    ] = rm.DVDuration(value="P1W")

    #  composition.set_all("language", code="en", terminology="ISO_639-1")
    #  composition.set_all("territory", code="it", terminology="ISO_3166-1")
    #  composition.set_all("composer", value="test")

    composition.set_defaults()
    flat = flatten(composition)
    assert "test/targeted_therapy_start/start_of_targeted_therapy/from_event" in flat


@pytest.mark.parametrize("backend", template_factory.backends())
def test_set_null_flavour(composition):
    null_flavour = rm.NullFlavour(value="unknown", code="253", terminology="openehr")
    composition[
        "/test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy/"
    ] = null_flavour
    flat = flatten(composition)
    assert (
        flat[
            "test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy/_null_flavour|value"
        ]
        == null_flavour.value
    )
    assert (
        flat[
            "test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy/_null_flavour|code"
        ]
        == null_flavour.code
    )
    assert (
        flat[
            "test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy/_null_flavour|terminology"
        ]
        == null_flavour.terminology
    )
    assert (
        flat[
            "test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy"
        ]
        == ""
    )
