#!/usr/bin/env python
# -*- coding: utf-8 -*-

from contextlib import redirect_stdout
import io
import json
import pytest
from flatehr.cli.generate import from_file
from flatehr.cli.inspect_template import main as inspect


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


@pytest.mark.parametrize("template_file", ("tests/resources/web_template.json",))
def test_inspect(template_file, expected_inspect):
    f = io.StringIO()
    with redirect_stdout(f):
        inspect(template_file, aql_path=True, inputs=True)
    stdout = f.getvalue()
    assert stdout == expected_inspect


def test_missing_aql_path(missing_aql_path_webtemplate):
    inspect(missing_aql_path_webtemplate, aql_path=True)
