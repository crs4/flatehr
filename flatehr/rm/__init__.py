#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flatehr.rm.models import *
from pipe import map


def get_model_class(class_name: str) -> type:

    from flatehr.rm import models

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

    return cls


class InvalidRMName(Exception):
    ...
