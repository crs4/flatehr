import json
from typing import Iterable

import pytest

from flatehr.flat import Composition, WebTemplateNode
from flatehr.http import OpenEHRClient
from flatehr.ingest import (
    BasicIngester,
    EHRCompositionMapping,
    Ingester,
    MultiThreadedIngester,
)


@pytest.fixture
def web_template_json():
    with open("tests/resources/web_template.json") as f_obj:
        return json.load(f_obj)


@pytest.fixture
def composition(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    return Composition(web_template)


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
