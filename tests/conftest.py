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
from flatehr.mappers import ValueMapper


@pytest.fixture
def web_template_json():
    with open("tests/resources/web_template.json") as f_obj:
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
    return ValueMapper({}, True)


@pytest.fixture
def template(backend, web_template_json):
    return template_factory(backend, web_template_json).get()


@pytest.fixture
def template_node(node_id, template):
    return template.root.get_descendant(node_id)
