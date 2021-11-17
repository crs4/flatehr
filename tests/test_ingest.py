import pytest
from flatehr.ingest import BasicIngester, MultiThreadedIngester


@pytest.mark.parametrize("n_compositions", [2])
def test_ingester(ingester, ehr_composition_mapping, n_compositions):
    ehr_composition_mapping = ehr_composition_mapping(n_compositions)
    success, fail = ingester.ingest(ehr_composition_mapping)
    assert success == n_compositions
    assert fail == 0
