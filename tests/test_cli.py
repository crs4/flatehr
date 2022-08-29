#!/usr/bin/env python
# -*- coding: utf-8 -*-

from contextlib import redirect_stdout
import io
import json
import pytest
from flatehr.cli.generate import from_file


@pytest.mark.parametrize(
    "input_file,template_file, conf_file",
    [
        (
            "tests/resources/source.xml",
            "tests/resources/web_template.json",
            "tests/resources/xml_conf.yaml",
        ),
        (
            "tests/resources/source.json",
            "tests/resources/web_template.json",
            "tests/resources/json_conf.yaml",
        ),
    ],
)
def test_from_file(input_file, template_file, conf_file, expected_composition):
    f = io.StringIO()
    with redirect_stdout(f):
        from_file(
            input_file,
            template_file=template_file,
            conf_file=conf_file,
            skip_ehr_id=True,
        )
    stdout = f.getvalue()
    assert json.loads(stdout) == expected_composition
