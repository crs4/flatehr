#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

import openehr_client.data_types as data_types
from openehr_client.flat import Composition, CompositionNode, WebTemplateNode


def test_web_template_node(web_template_json):
    WebTemplateNode.create(web_template_json)


@pytest.mark.skip("Composition.get TBD")
def test_composition_get_path(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    text = 'ok'
    path = '/test/context/status'
    composition.create_node(path, text)
    node = composition.get(path)
    assert isinstance(node.value, data_types.Text)


def test_composition_set_path_dv_text(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    text = 'ok'
    path = 'test/context/status'
    node = composition.create_node(path, text)
    assert isinstance(node, CompositionNode)
    assert isinstance(node.value, data_types.Text)
    assert node.value.value == text

    flat = composition.as_flat()
    assert flat == {path: text}


def test_composition_set_path_code_phrase(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    terminology = 'ISO_639-1'
    code = 'en'
    path = 'test/language'

    node = composition.create_node(path, terminology=terminology, code=code)
    assert isinstance(node.value, data_types.CodePhrase)
    assert node.value.terminology == terminology
    assert node.value.code == code

    flat = composition.as_flat()
    assert flat == {f'{path}|code': code, f'{path}|terminology': terminology}


def test_composition_set_path_dv_coded_text(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    text = 'ok'
    terminology = 'ISO_639-1'
    code = 'en'
    path = 'test/context/setting'
    node = composition.create_node(path,
                                   text,
                                   terminology=terminology,
                                   code=code)
    assert isinstance(node.value, data_types.CodedText)

    assert node.value.value == text
    assert node.value.terminology == terminology
    assert node.value.code == code

    flat = composition.as_flat()
    assert flat == {
        f'{path}|code': code,
        f'{path}|terminology': terminology,
        f'{path}|value': text
    }


def test_composition_set_path_dv_datetime(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    text = '2021-04-22T10:19:49.915Z'
    path = 'test/context/start_time'
    node = composition.create_node(path, text)
    assert isinstance(node.value, data_types.DateTime)
    assert node.value.value == text

    flat = composition.as_flat()
    assert flat == {path: text}


def test_composition_set_path_party_proxy(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    name = 'composer'
    path = 'test/composer'
    node = composition.create_node(path, name)
    assert isinstance(node.value, data_types.PartyProxy)
    assert node.value.name == name

    flat = composition.as_flat()
    assert flat == {f'{path}|name': name}


def test_composition_to_flat(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    text = 'ok'
    path_status = 'test/context/status'
    composition.create_node(path_status, text)

    terminology = 'ISO_639-1'
    code = 'en'
    path_lang = 'test/language'

    composition.create_node(path_lang, terminology=terminology, code=code)

    flat = composition.as_flat()
    assert flat == {
        path_status: text,
        f'{path_lang}|code': code,
        f'{path_lang}|terminology': terminology
    }


def test_composition_add_multiple_instances(composition):
    for i in range(2):
        event = composition.create_node(
            'test/lab_result_details/result_group/laboratory_test_result/any_event'
        )
        event.create_node('test_name', f'test-{i}')
    assert composition.as_flat() == {
        'test/lab_result_details/result_group/laboratory_test_result/any_event:0/test_name':
        'test-0',
        'test/lab_result_details/result_group/laboratory_test_result/any_event:1/test_name':
        'test-1',
    }


def test_composition_set_default(composition):
    terminology = 'ISO_639-1'
    code = 'en'
    composition.set_default('language', code=code, terminology=terminology)

    path_lang = 'test/language'
    flat = composition.as_flat()
    assert flat == {
        f'{path_lang}|code': code,
        f'{path_lang}|terminology': terminology
    }

    path_lab_test_result = 'test/lab_result_details/result_group/laboratory_test_result'
    composition.create_node(path_lab_test_result)
    composition.set_default('language', code=code, terminology=terminology)
    flat = composition.as_flat()
    print(flat)
    assert flat == {
        f'{path_lang}|code': code,
        f'{path_lang}|terminology': terminology,
        f'{path_lab_test_result}/language|code': code,
        f'{path_lab_test_result}/language|terminology': terminology,
    }

    for i in range(2):
        event = composition.create_node(
            'test/lab_result_details/result_group/laboratory_test_result/any_event'
        )
        composition.set_default('test_name', 'test_name')
    assert composition.as_flat() == {
        f'{path_lang}|code':
        code,
        f'{path_lang}|terminology':
        terminology,
        f'{path_lab_test_result}/language|code':
        code,
        f'{path_lab_test_result}/language|terminology':
        terminology,
        'test/lab_result_details/result_group/laboratory_test_result/any_event:0/test_name':
        'test_name',
        'test/lab_result_details/result_group/laboratory_test_result/any_event:1/test_name':
        'test_name',
    }
