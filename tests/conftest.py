#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import pytest


@pytest.fixture
def web_template_json():
    with open('tests/resources/web_template.json') as f_obj:
        return json.load(f_obj)
