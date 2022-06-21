import pytest
from flatehr import template_factory


@pytest.mark.parametrize("backend", template_factory.backends())
@pytest.mark.parametrize("web_template_path", ["./tests/resources/web_template.json"])
@pytest.mark.parametrize("n_compositions", [2])
def test_ingester(ingester, ehr_composition_mapping, n_compositions):
    ehr_composition_mapping = ehr_composition_mapping(n_compositions)
    success, fail = ingester.ingest(ehr_composition_mapping)
    assert success == n_compositions
    assert fail == 0
