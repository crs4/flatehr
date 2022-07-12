import json
from typing import Iterable

import pytest

from flatehr import template_factory, composition_factory
from flatehr.http import OpenEHRClient
from flatehr.ingest import (
    BasicIngester,
    EHRCompositionMapping,
    Ingester,
    MultiThreadedIngester,
)
from flatehr.core import TemplatePath
from flatehr.integration.sources import XPath, XPathSource


@pytest.fixture
def web_template_json(web_template_path):
    with open(web_template_path) as f_obj:
        return json.load(f_obj)


@pytest.fixture
def composition(template, backend):
    return composition_factory(backend, template).get()


@pytest.fixture
def client() -> OpenEHRClient:
    return OpenEHRClient("http://localhost:8080", dry_run=True)


@pytest.fixture
def ehr_composition_mapping(
    composition, n_compositions
) -> Iterable[EHRCompositionMapping]:
    def _ehr_composition_mapping(n_compositions):
        return [EHRCompositionMapping(composition, i) for i in range(n_compositions)]

    return _ehr_composition_mapping


@pytest.fixture(params=[BasicIngester, MultiThreadedIngester])
def ingester(request) -> Ingester:
    return request.param(client=OpenEHRClient("localhost:8080", dry_run=True))


@pytest.fixture
def value_mapper():
    return ValueConverter({}, True)


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


@pytest.fixture
def xml_mapper(template, xml):
    return XPathSource(
        [
            XPath("//ns:Identifier/text()"),
            XPath("//ns:Event[@eventtype='Histopathology']"),
            XPath("//ns:Dataelement_58_2/text()"),
        ],
        xml,
    )
