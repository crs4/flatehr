#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import pytest

import flatehr.data_types as data_types
from flatehr.factory import composition_factory, template_factory
from flatehr.composition import Composition, CompositionNode

logging.basicConfig(level=logging.DEBUG)


@pytest.mark.parametrize("backend", composition_factory.backends())
def test_factory(composition, template):
    assert isinstance(composition, Composition)
    assert composition.template == template
    assert composition.as_flat() == {}


@pytest.mark.parametrize("backend", template_factory.backends())
def test_composition_create_dv_text(composition):
    text = "ok"
    path = "test/context/status"
    composition[path] = data_types.Text(text)

    flat = composition.as_flat()
    assert flat == {path: text}


@pytest.mark.parametrize("backend", template_factory.backends())
def test_composition_add_multiple_instances(composition):
    path = "test/lab_result_details/result_group/laboratory_test_result/any_event"

    composition[f"{path}/test_name"] = data_types.Text("test-0")

    assert composition.as_flat() == {f"{path}:0/test_name": "test-0"}

    composition[f"{path}/test_name"] = data_types.Text("test-0-0")
    assert composition.as_flat() == {f"{path}:0/test_name": "test-0-0"}

    composition.add(path)
    composition[f"{path}/test_name"] = data_types.Text("test-1")

    assert composition.as_flat() == {
        f"{path}:0/test_name": "test-0-0",
        f"{path}:1/test_name": "test-1",
    }

    composition[f"{path}:0/test_name"] = data_types.Text("test-0-0-0")
    assert composition.as_flat() == {
        f"{path}:0/test_name": "test-0-0-0",
        f"{path}:1/test_name": "test-1",
    }


#  @pytest.mark.parametrize("backend", template_factory.backends())
#  def test_composition_create_dv_text_with_default(composition):
#      path = "test/targeted_therapy_start/start_of_targeted_therapy/from_event"
#      node = composition.create_node(path)
#      assert node.value.value == "Primary diagnosis"


#
#  def test_composition_create_code_phrase(web_template_json):
#      web_template = WebTemplateNode.create(web_template_json)
#      composition = Composition(web_template)
#      terminology = "ISO_639-1"
#      code = "en"
#      path = "language"
#
#      node = composition.create_node(path, terminology=terminology, code=code)
#      assert isinstance(node.value, data_types.CodePhrase)
#      assert node.value.terminology == terminology
#      assert node.value.code == code
#
#      flat = composition.as_flat()
#      assert flat == {
#          f"{composition.root.name}/{path}|code": code,
#          f"{composition.root.name}/{path}|terminology": terminology,
#      }
#
#
#  def test_composition_create_dv_coded_text(web_template_json):
#      web_template = WebTemplateNode.create(web_template_json)
#      composition = Composition(web_template)
#      text = "ok"
#      terminology = "ISO_639-1"
#      code = "en"
#      path = "context/setting"
#      node = composition.create_node(path, value=text, terminology=terminology, code=code)
#      assert isinstance(node.value, data_types.CodedText)
#
#      assert node.value.value == text
#      assert node.value.terminology == terminology
#      assert node.value.code == code
#
#      flat = composition.as_flat()
#      assert flat == {
#          f"{composition.root.name}/{path}|code": code,
#          f"{composition.root.name}/{path}|terminology": terminology,
#          f"{composition.root.name}/{path}|value": text,
#      }
#
#
#  def test_composition_create_dv_datetime(web_template_json):
#      web_template = WebTemplateNode.create(web_template_json)
#      composition = Composition(web_template)
#      path = "context/start_time"
#      node = composition.create_node(path, year=2021, month=4, day=22)
#      assert isinstance(node.value, data_types.DateTime)
#
#      flat = composition.as_flat()
#      text = "2021-04-22T00:00:00"
#      assert flat == {f"{composition.root.name}/{path}": text}
#
#
#  def test_composition_create_party_proxy(web_template_json):
#      web_template = WebTemplateNode.create(web_template_json)
#      composition = Composition(web_template)
#      name = "composer"
#      path = "composer"
#      node = composition.create_node(path, value=name)
#      assert isinstance(node.value, data_types.PartyProxy)
#      assert node.value.value == name
#
#      flat = composition.as_flat()
#      assert flat == {f"{composition.root.name}/{path}|name": name}
#
#
#  def test_composition_to_flat(web_template_json):
#      web_template = WebTemplateNode.create(web_template_json)
#      composition = Composition(web_template)
#      text = "ok"
#      path_status = "context/status"
#      composition.create_node(path_status, value=text)
#
#      terminology = "ISO_639-1"
#      code = "en"
#      path_lang = "language"
#
#      composition.create_node(path_lang, terminology=terminology, code=code)
#
#      flat = composition.as_flat()
#      assert flat == {
#          f"{composition.root.name}/{path_status}": text,
#          f"{composition.root.name}/{path_lang}|code": code,
#          f"{composition.root.name}/{path_lang}|terminology": terminology,
#      }
#
#

#
#  def test_composition_not_increment_cardinality(composition):
#      for i, child in enumerate(["test_name", "test_diagnosis"]):
#          event = composition.create_node(
#              "lab_result_details/result_group/laboratory_test_result/any_event", False
#          )
#          event.create_node(child, value=f"test-{i}")
#      assert composition.as_flat() == {
#          "test/lab_result_details/result_group/laboratory_test_result/any_event:0/test_name": "test-0",
#          "test/lab_result_details/result_group/laboratory_test_result/any_event:0/test_diagnosis:0": "test-1",
#      }
#
#
#  def test_composition_set_all(composition):
#      terminology = "ISO_639-1"
#      code = "en"
#      composition.set_all("language", code=code, terminology=terminology)
#
#      path_lang = "language"
#      flat = composition.as_flat()
#      assert flat == {
#          f"{composition.root.name}/{path_lang}|code": code,
#          f"{composition.root.name}/{path_lang}|terminology": terminology,
#      }
#
#      path_lab_test_result = "lab_result_details/result_group/laboratory_test_result"
#      composition.create_node(path_lab_test_result)
#      composition.set_all("language", code=code, terminology=terminology)
#      flat = composition.as_flat()
#      assert flat == {
#          f"{composition.root.name}/{path_lang}|code": code,
#          f"{composition.root.name}/{path_lang}|terminology": terminology,
#          f"{composition.root.name}/{path_lab_test_result}/language|code": code,
#          f"{composition.root.name}/{path_lab_test_result}/language|terminology": terminology,
#      }
#
#      for _ in range(2):
#          composition.create_node(
#              "lab_result_details/result_group/laboratory_test_result/any_event"
#          )
#          composition.set_all("test_name", value="test_name")
#      assert composition.as_flat() == {
#          f"{composition.root.name}/{path_lang}|code": code,
#          f"{composition.root.name}/{path_lang}|terminology": terminology,
#          f"{composition.root.name}/{path_lab_test_result}/language|code": code,
#          f"{composition.root.name}/{path_lab_test_result}/language|terminology": terminology,
#          "test/lab_result_details/result_group/laboratory_test_result/any_event:0/test_name": "test_name",
#          "test/lab_result_details/result_group/laboratory_test_result/any_event:1/test_name": "test_name",
#      }
#
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
