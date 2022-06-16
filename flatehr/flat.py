import logging
from functools import singledispatch
from typing import Dict

from deepdiff import DeepDiff
from flatehr.composition import Composition
from flatehr.rm import NullFlavour

from flatehr.rm.models import (
    CodePhrase,
    DVCodedText,
    DVDateTime,
    DVDuration,
    DVText,
    PartyIdentified,
)

logger = logging.getLogger("flatehr")


@singledispatch
def flatten(*args) -> Dict:
    ...


@flatten.register
def _flatten_composition(composition: Composition) -> Dict:
    flat = {}
    for leaf in composition.root.leaves:
        if leaf.template.is_leaf:
            flat.update(flatten(leaf.value, str(leaf)))
    return flat


@flatten.register(DVText)
@flatten.register(DVDateTime)
@flatten.register(DVDuration)
def _flatten_simple_value(model, path: str) -> Dict:
    return {f"{path.strip('/')}": model.value}


@flatten.register
def _flatten_code_phrase(model: CodePhrase, path: str) -> Dict:
    dct = {
        f"{path}|code": model.code_string,
        f"{path}|terminology": model.terminology_id.value,
    }
    if model.preferred_term:
        dct[f"{path}|preferred_term"] = model.preferred_term
    return dct


@flatten.register
def _flatten_dv_coded_text(model: DVCodedText, path: str) -> Dict:
    dct = _flatten_code_phrase(model.defining_code, path)
    dct[f"{path}|value"] = model.value
    return dct


@flatten.register
def _flatten_party_identified(model: PartyIdentified, path: str) -> Dict:
    return {f"{path.strip('/')}|name": model.name}


@flatten.register
def _flatten_null_flavour(model: NullFlavour, path: str) -> Dict:
    flat = {}
    flat[f"{path}/_null_flavour|value"] = model.value
    flat[f"{path}/_null_flavour|code"] = model.code
    flat[f"{path}/_null_flavour|terminology"] = model.terminology

    flat[path] = model.place_holder
    return flat


def diff(flat_1: Dict, flat_2: Dict):
    return DeepDiff(flat_1, flat_2, verbose_level=2)
