import json

import pytest

from flatehr import template_factory, composition_factory
from flatehr.cli.generate import conf_from_file


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
def xml_source():
    return "tests/resources/source.xml"


@pytest.fixture
def json_source():
    return "tests/resources/source.json"


@pytest.fixture
def complex_template():
    return "tests/resources/complex_template.json"


@pytest.fixture
def conf():
    return conf_from_file("tests/resources/xml_conf.yaml")


@pytest.fixture
def source_kvs():
    return iter([("//ns:Dataelement_3_1/text()", "10")])


@pytest.fixture
def expected_composition():
    with open("tests/resources/expected_composition.json") as f:
        return json.load(f)


@pytest.fixture
def expected_inspect():
    with open("tests/resources/expected_inspect.txt") as f:
        return f.read()
