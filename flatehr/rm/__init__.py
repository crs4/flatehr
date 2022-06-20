#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from pipe import map
from pydantic import BaseModel


class RMObject(BaseModel):
    ...


from flatehr.rm.models import *


@dataclass
class NullFlavour:
    # place_holder is a workaround for ehrbase expecting value even in case of NullFlavour
    # (at least for some data types)
    value: str
    code: str
    terminology: str
    place_holder: str = ""

    @staticmethod
    def get_default(place_holder=""):
        return NullFlavour("unknown", "253", "openehr", place_holder)


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
