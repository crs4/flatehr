#!/usr/bin/env python
# -*- coding: utf-8 -*-
from openehr_client.flat import Composition, WebTemplateNode


def test_web_template_node(web_template_json):
    WebTemplateNode.create(web_template_json)


def test_composition(web_template_json):
    web_template = WebTemplateNode.create(web_template_json)
    composition = Composition(web_template)
    event0 = composition.root.add_descendant(
        'molecular_markers/result_group/oncogenic_mutations_test/any_event')
    event0.add_descendant('braf_pic3ca_her2_mutation_status').value = 1
    composition.root.add_descendant(
        'molecular_markers/result_group/oncogenic_mutations_test/any_event/braf_pic3ca_her2_mutation_status'
    ).value = 2
