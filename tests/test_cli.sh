#!/usr/bin/env bash
set -xe
flatehr generate from-file -t tests/resources/web_template.json -c tests/resources/xml_conf.yaml tests/resources/source.xml
