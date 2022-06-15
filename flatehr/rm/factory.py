#!/usr/bin/env python
# -*- coding: utf-8 -*-


import pinject
from pipe import map

from flatehr.rm import get_model_class, models


class BindingSpec(pinject.BindingSpec):
    def __init__(self, values, *args, **kwargs):
        self.values = values
        super().__init__(*args, **kwargs)

    def configure(self, bind):
        for k, v in self.values.items():
            bind(k, to_instance=v)


obj_graph = pinject.new_object_graph(
    binding_specs=[
        BindingSpec({"value": "value", "code_string": "cs", "preferred_term": "pf"})
    ]
)


def factory(class_name: str, **kwargs):
    obj_graph = pinject.new_object_graph(binding_specs=[BindingSpec(kwargs)])

    cls = get_model_class(class_name)
    return obj_graph.provide(cls)
