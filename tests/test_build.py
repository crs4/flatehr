#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from flatehr.build import build_composition
from flatehr.core import flat
from flatehr.factory import template_factory


@pytest.mark.parametrize("backend", template_factory.backends())
@pytest.mark.parametrize("web_template_path", ["./tests/resources/web_template.json"])
def test_build_composition(conf, template, source_kvs):
    composition, ctx, ehr_id = build_composition(conf, template, source_kvs)
    flat_composition = flat(composition, ctx)

    assert flat_composition == {
        "test/patient_data/primary_diagnosis/primary_diagnosis/_null_flavour|code": "253",
        "test/patient_data/primary_diagnosis/primary_diagnosis/_null_flavour|terminology": "openehr",
        "test/patient_data/primary_diagnosis/primary_diagnosis/_null_flavour|value": "unknown",
        "test/patient_data/primary_diagnosis/diagnosis_timing/primary_diagnosis:0/age_at_diagnosis": "P10Y",
        "test/patient_data/gender/biological_sex/_null_flavour|value": "unknown",
        "test/patient_data/gender/biological_sex/_null_flavour|code": 253,
        "test/patient_data/gender/biological_sex/_null_flavour|terminology": "openehr",
        "ctx/language": "en",
        "ctx/composer_name": "test",
        "ctx/subject|name": "42112",
        "ctx/encoding|code": "UTF-8",
        "ctx/encoding|terminology": "IANA_character-sets",
    }
