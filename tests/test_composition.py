#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import pytest

import flatehr.data_types as data_types
from flatehr.composition import Composition, IncompatibleDataType, NotaLeaf
from flatehr.factory import composition_factory, template_factory

logging.basicConfig(level=logging.DEBUG)


@pytest.mark.parametrize("backend", composition_factory.backends())
def test_factory(composition, template):
    assert isinstance(composition, Composition)
    assert composition.template == template
    assert composition.as_flat() == {}


@pytest.mark.parametrize("backend", template_factory.backends())
def test_create_dv_text(composition):
    text = "ok"
    path = "test/context/status"
    composition[path] = data_types.DV_TEXT(text)

    flat = composition.as_flat()
    assert flat == {path: text}


@pytest.mark.parametrize("backend", template_factory.backends())
def test_not_a_leaf(composition):
    text = "ok"
    path = "test/context"
    with pytest.raises(NotaLeaf):
        composition[path] = data_types.DV_TEXT(text)


@pytest.mark.parametrize("backend", template_factory.backends())
def test_incompatible_data_type(composition):
    path = "test/context/status"
    with pytest.raises(IncompatibleDataType):
        composition[path] = data_types.DV_DATE_TIME(year=2001)


@pytest.mark.parametrize("backend", template_factory.backends())
def test_composition_add_multiple_instances(composition):
    path = "test/lab_result_details/result_group/laboratory_test_result/any_event"

    composition[f"{path}/test_name"] = data_types.DV_TEXT("test-0")

    assert composition.as_flat() == {f"{path}:0/test_name": "test-0"}

    composition[f"{path}/test_name"] = data_types.DV_TEXT("test-0-0")
    assert composition.as_flat() == {f"{path}:0/test_name": "test-0-0"}

    composition.add(path)
    composition[f"{path}/test_name"] = data_types.DV_TEXT("test-1")

    assert composition.as_flat() == {
        f"{path}:0/test_name": "test-0-0",
        f"{path}:1/test_name": "test-1",
    }

    composition[f"{path}:0/test_name"] = data_types.DV_TEXT("test-0-0-0")
    assert composition.as_flat() == {
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

    composition[path] = data_types.CODE_PHRASE(terminology=terminology, code=code)
    value = composition[path]
    assert isinstance(value, data_types.CODE_PHRASE)
    assert value.terminology == terminology
    assert value.code == code

    flat = composition.as_flat()
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
    composition[path] = data_types.DV_CODED_TEXT(
        value=text, terminology=terminology, code=code
    )
    value = composition[path]
    assert isinstance(value, data_types.DV_CODED_TEXT)

    assert value.value == text
    assert value.terminology == terminology
    assert value.code == code

    flat = composition.as_flat()
    assert flat == {
        f"{path}|code": code,
        f"{path}|terminology": terminology,
        f"{path}|value": text,
    }


@pytest.mark.parametrize("backend", template_factory.backends())
def test_composition_create_dv_datetime(composition):
    path = "test/context/start_time"
    composition[path] = data_types.DV_DATE_TIME(year=2021, month=4, day=22)
    value = composition[path]
    assert isinstance(value, data_types.DV_DATE_TIME)

    flat = composition.as_flat()
    text = "2021-04-22T00:00:00"
    assert flat == {f"{path}": text}


@pytest.mark.parametrize("backend", template_factory.backends())
def test_composition_create_party_proxy(composition):
    name = "composer"
    path = "test/composer"
    composition[path] = data_types.PARTY_PROXY(name)
    value = composition[path]
    assert isinstance(value, data_types.PARTY_PROXY)
    assert value.value == name

    flat = composition.as_flat()
    assert flat == {f"{path}|name": name}


@pytest.mark.parametrize("backend", template_factory.backends())
def test_composition_to_flat(composition):
    text = "ok"
    path_status = "test/context/status"
    composition[path_status] = data_types.DV_TEXT(text)

    terminology = "ISO_639-1"
    code = "en"
    path_lang = "test/language"

    composition[path_lang] = data_types.CODE_PHRASE(terminology=terminology, code=code)

    flat = composition.as_flat()
    assert flat == {
        f"{path_status}": text,
        f"{path_lang}|code": code,
        f"{path_lang}|terminology": terminology,
    }


@pytest.mark.parametrize("backend", template_factory.backends())
def test_composition_set_all(composition):
    terminology = "ISO_639-1"
    code = "en"
    #  __import__("pudb").set_trace()
    composition["**/language"] = data_types.CODE_PHRASE(
        code=code, terminology=terminology
    )

    path_lang = "test/language"

    flat = composition.as_flat()
    assert flat == {f"{path_lang}|code": code, f"{path_lang}|terminology": terminology}

    path_lab_test_result = (
        "test/lab_result_details/result_group/laboratory_test_result/any_event"
    )

    for _ in range(2):
        composition.add(path_lab_test_result)

    composition["**/test_name"] = data_types.DV_TEXT("test_name")
    assert composition.as_flat() == {
        f"{path_lang}|code": code,
        f"{path_lang}|terminology": terminology,
        f"{path_lab_test_result}:0/test_name": "test_name",
        f"{path_lab_test_result}:1/test_name": "test_name",
    }


#
#  @pytest.mark.skip("TBD")
#  def test_web_template_node(web_template_json):
#      WebTemplateNode.create(web_template_json)
#
#
#  @pytest.mark.skip("Composition.get TBD")
#  def test_composition_get_path(web_template_json):
#      web_template = WebTemplateNode.create(web_template_json)
#      composition = Composition(web_template)
#      text = "ok"
#      path = "/test/context/status"
#      composition.create_node(path, value=text)
#      node = composition.get(path)
#      assert isinstance(node.value, data_types.Text)
#
#
#  def test_composition_set_defaults(composition):
#      composition.create_node(
#          "/test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy/",
#          value="P1W",
#      )
#
#      composition.set_all("language", code="en", terminology="ISO_639-1")
#      composition.set_all("territory", code="it", terminology="ISO_3166-1")
#      composition.set_all("composer", value="test")
#
#      composition.set_defaults()
#      flat = composition.as_flat()
#      assert "test/targeted_therapy_start/start_of_targeted_therapy/from_event" in flat
#
#
#  def test_set_null_flavour(composition):
#      null_flavour = data_types.NullFlavour(
#          value="unknown", code="253", terminology="openehr"
#      )
#      composition.create_node(
#          "/test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy/",
#          null_flavour=null_flavour,
#      )
#      flat = composition.as_flat()
#      assert (
#          flat[
#              "test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy/_null_flavour|value"
#          ]
#          == null_flavour.value
#      )
#      assert (
#          flat[
#              "test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy/_null_flavour|code"
#          ]
#          == null_flavour.code
#      )
#      assert (
#          flat[
#              "test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy/_null_flavour|terminology"
#          ]
#          == null_flavour.terminology
#      )
#      assert (
#          flat[
#              "test/targeted_therapy_start/start_of_targeted_therapy/date_of_start_of_targeted_therapy"
#          ]
#          == ""
#      )
