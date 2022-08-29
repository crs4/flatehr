#!/usr/bin/env bash
set -e

xml_comp=$(flatehr generate from-file -t tests/resources/web_template.json -c tests/resources/xml_conf.yaml --skip-ehr-id tests/resources/source.xml)
json_comp=$(flatehr generate from-file -t tests/resources/web_template.json -c tests/resources/json_conf.yaml --skip-ehr-id tests/resources/source.json)

expected=$(cat tests/resources/expected_composition.json)
[[  "$xml_comp" == "$expected" ]]
[[  "$json_comp" == "$expected" ]]
