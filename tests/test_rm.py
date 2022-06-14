#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict

import pytest

from flatehr.rm.factory import factory
from flatehr.rm.models import CodePhrase, DVText


dv_text_values = {"value": "test"}
code_phrase_values = {**dv_text_values, "code_string": "code_string"}


@pytest.mark.parametrize(
    "class_name,values", [("DVText", dv_text_values), ("DV_TEXT", dv_text_values)]
)
def test_factory_dv_text(class_name, values: Dict):
    model = factory(class_name, **values)
    assert type(model) == DVText
    assert model.value == values["value"]


@pytest.mark.parametrize(
    "class_name,values",
    [("CodePhrase", code_phrase_values), ("CODE_PHRASE", code_phrase_values)],
)
def test_factory_code_phase(class_name, values: Dict):
    model = factory(class_name, **values)
    assert type(model) == CodePhrase
    assert model.terminology_id.value == code_phrase_values["value"]
    assert model.code_string == code_phrase_values["code_string"]
