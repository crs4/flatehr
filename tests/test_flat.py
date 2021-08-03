#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

import openehr_client.data_types as data_types
from openehr_client.flat import Composition, WebTemplateNode


def test_web_template_node(web_template_json):
    WebTemplateNode.create(web_template_json)


@pytest.mark.skip("Composition.get TBD")
def test_composition_set_path(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    text = 'ok'
    path = '/test/context/status'
    composition.set(path, text)
    node = composition.get(path)
    assert isinstance(node.value, data_types.Text)


def test_composition_set_path_dv_text(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    text = 'ok'
    node = composition.set('/test/context/status', text)
    assert isinstance(node.value, data_types.Text)
    assert node.value.value == text


def test_composition_set_path_code_phrase(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    terminology = 'ISO_639-1'
    code = 'en'
    node = composition.set('/test/language',
                           terminology=terminology,
                           code=code)
    assert isinstance(node.value, data_types.CodePhrase)
    assert node.value.terminology == terminology
    assert node.value.code == code


def test_composition_set_path_dv_coded_text(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    text = 'ok'
    terminology = 'ISO_639-1'
    code = 'en'
    node = composition.set('/test/context/setting',
                           text,
                           terminology=terminology,
                           code=code)
    assert isinstance(node.value, data_types.CodedText)
    assert node.value.value == text
    assert node.value.terminology == terminology
    assert node.value.code == code


def test_composition_set_path_dv_datetime(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    text = '2021-04-22T10:19:49.915Z'
    node = composition.set('/test/context/start_time', text)
    assert isinstance(node.value, data_types.DateTime)
    assert node.value.value == text
