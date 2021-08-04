import json

import pytest

from openehr_client.flat import Composition, WebTemplateNode


@pytest.fixture
def web_template_json():
    with open('tests/resources/web_template.json') as f_obj:
        return json.load(f_obj)


@pytest.fixture
def composition(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    return Composition(web_template)
