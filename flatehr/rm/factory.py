#!/usr/bin/env python
# -*- coding: utf-8 -*-


import pinject
from pipe import map

from flatehr.rm import models


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
    alternative_name = "".join(
        class_name.split("_") | map(lambda el: el.capitalize() if el != "DV" else el)
    )
    try:
        cls = getattr(models, class_name)
    except AttributeError:

        try:
            cls = getattr(models, alternative_name)
        except AttributeError as ex:
            raise InvalidRMName(
                f"tried {class_name}, {alternative_name}, both failed"
            ) from ex

    obj_graph = pinject.new_object_graph(binding_specs=[BindingSpec(kwargs)])
    return obj_graph.provide(cls)


class InvalidRMName(Exception):
    ...
