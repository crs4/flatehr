#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import pytest

import flatehr.data_types as data_types
from flatehr.flat import Composition, CompositionNode, WebTemplateNode

logging.basicConfig(level=logging.DEBUG)


def test_composition_create_dv_text(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    text = 'ok'
    path = 'context/status'
    node = composition.create_node(path, value=text)
    assert isinstance(node, CompositionNode)
    assert isinstance(node.value, data_types.Text)
    assert node.value.value == text

    flat = composition.as_flat()
    assert flat == {f'test/{path}': text}


def test_composition_create_code_phrase(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    terminology = 'ISO_639-1'
    code = 'en'
    path = 'language'

    node = composition.create_node(path, terminology=terminology, code=code)
    assert isinstance(node.value, data_types.CodePhrase)
    assert node.value.terminology == terminology
    assert node.value.code == code

    flat = composition.as_flat()
    assert flat == {
        f'{composition.root.name}/{path}|code': code,
        f'{composition.root.name}/{path}|terminology': terminology
    }


def test_composition_create_dv_coded_text(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    text = 'ok'
    terminology = 'ISO_639-1'
    code = 'en'
    path = 'context/setting'
    node = composition.create_node(path,
                                   value=text,
                                   terminology=terminology,
                                   code=code)
    assert isinstance(node.value, data_types.CodedText)

    assert node.value.value == text
    assert node.value.terminology == terminology
    assert node.value.code == code

    flat = composition.as_flat()
    assert flat == {
        f'{composition.root.name}/{path}|code': code,
        f'{composition.root.name}/{path}|terminology': terminology,
        f'{composition.root.name}/{path}|value': text
    }


def test_composition_create_dv_datetime(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    path = 'context/start_time'
    node = composition.create_node(path, year=2021, month=4, day=22)
    assert isinstance(node.value, data_types.DateTime)

    flat = composition.as_flat()
    text = '2021-04-22T00:00:00'
    assert flat == {f'{composition.root.name}/{path}': text}


def test_composition_create_party_proxy(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    name = 'composer'
    path = 'composer'
    node = composition.create_node(path, value=name)
    assert isinstance(node.value, data_types.PartyProxy)
    assert node.value.value == name

    flat = composition.as_flat()
    assert flat == {f'{composition.root.name}/{path}|name': name}


def test_composition_to_flat(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    text = 'ok'
    path_status = 'context/status'
    composition.create_node(path_status, value=text)

    terminology = 'ISO_639-1'
    code = 'en'
    path_lang = 'language'

    composition.create_node(path_lang, terminology=terminology, code=code)

    flat = composition.as_flat()
    assert flat == {
        f'{composition.root.name}/{path_status}': text,
        f'{composition.root.name}/{path_lang}|code': code,
        f'{composition.root.name}/{path_lang}|terminology': terminology
    }


def test_composition_add_multiple_instances(composition):
    for i in range(2):
        event = composition.create_node(
            'lab_result_details/result_group/laboratory_test_result/any_event')
        event.create_node('test_name', value=f'test-{i}')
    assert composition.as_flat() == {
        'test/lab_result_details/result_group/laboratory_test_result/any_event:0/test_name':
        'test-0',
        'test/lab_result_details/result_group/laboratory_test_result/any_event:1/test_name':
        'test-1',
    }


def test_composition_not_increment_cardinality(composition):
    for i, child in enumerate(['test_name', 'test_diagnosis']):
        event = composition.create_node(
            'lab_result_details/result_group/laboratory_test_result/any_event',
            False)
        event.create_node(child, value=f'test-{i}')
    assert composition.as_flat() == {
        'test/lab_result_details/result_group/laboratory_test_result/any_event:0/test_name':
        'test-0',
        'test/lab_result_details/result_group/laboratory_test_result/any_event:0/test_diagnosis:0':
        'test-1',
    }


def test_composition_set_default(composition):
    terminology = 'ISO_639-1'
    code = 'en'
    composition.set_default('language', code=code, terminology=terminology)

    path_lang = 'language'
    flat = composition.as_flat()
    assert flat == {
        f'{composition.root.name}/{path_lang}|code': code,
        f'{composition.root.name}/{path_lang}|terminology': terminology
    }

    path_lab_test_result = 'lab_result_details/result_group/laboratory_test_result'
    composition.create_node(path_lab_test_result)
    composition.set_default('language', code=code, terminology=terminology)
    flat = composition.as_flat()
    print(flat)
    assert flat == {
        f'{composition.root.name}/{path_lang}|code':
        code,
        f'{composition.root.name}/{path_lang}|terminology':
        terminology,
        f'{composition.root.name}/{path_lab_test_result}/language|code':
        code,
        f'{composition.root.name}/{path_lab_test_result}/language|terminology':
        terminology,
    }

    for _ in range(2):
        composition.create_node(
            'lab_result_details/result_group/laboratory_test_result/any_event')
        composition.set_default('test_name', value='test_name')
    assert composition.as_flat() == {
        f'{composition.root.name}/{path_lang}|code':
        code,
        f'{composition.root.name}/{path_lang}|terminology':
        terminology,
        f'{composition.root.name}/{path_lab_test_result}/language|code':
        code,
        f'{composition.root.name}/{path_lab_test_result}/language|terminology':
        terminology,
        'test/lab_result_details/result_group/laboratory_test_result/any_event:0/test_name':
        'test_name',
        'test/lab_result_details/result_group/laboratory_test_result/any_event:1/test_name':
        'test_name',
    }


@pytest.mark.skip("TBD")
def test_web_template_node(web_template_json):
    WebTemplateNode.create(web_template_json)


@pytest.mark.skip("Composition.get TBD")
def test_composition_get_path(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    text = 'ok'
    path = '/test/context/status'
    composition.create_node(path, value=text)
    node = composition.get(path)
    assert isinstance(node.value, data_types.Text)
