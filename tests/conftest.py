import json

import pytest

from flatehr import template_factory, composition_factory


@pytest.fixture
def web_template_json(web_template_path):
    with open(web_template_path) as f_obj:
        return json.load(f_obj)


@pytest.fixture
def composition(template, backend):
    return composition_factory(backend, template).get()


@pytest.fixture
def template(backend, web_template_json):
    return template_factory(backend, web_template_json).get()


@pytest.fixture
def template_node(path, template):
    return template[path]


@pytest.fixture
def xml():
    return "tests/resources/test.xml"


@pytest.fixture
def complex_template():
    return "tests/resources/complex_template.json"
