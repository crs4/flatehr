import logging
from functools import singledispatch
from typing import Dict

from deepdiff import DeepDiff
from flatehr.core import Composition
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
def flat(*args) -> Dict:
    raise NotImplementedError()


@flat.register
def _flat_composition(composition: Composition) -> Dict:
    _flat = {}
    for leaf in composition.root.leaves:
        if leaf.template.is_leaf:
            _flat.update(flat(leaf.value, str(leaf)))
    return _flat


@flat.register(DVText)
@flat.register(DVDateTime)
@flat.register(DVDuration)
def _flat_simple_value(model, path: str) -> Dict:
    return {f"{path.strip('/')}": model.value}


@flat.register
def _flat_code_phrase(model: CodePhrase, path: str) -> Dict:
    dct = {
        f"{path}|code": model.code_string,
        f"{path}|terminology": model.terminology_id.value,
    }
    if model.preferred_term:
        dct[f"{path}|preferred_term"] = model.preferred_term
    return dct


@flat.register
def _flat_dv_coded_text(model: DVCodedText, path: str) -> Dict:
    dct = _flat_code_phrase(model.defining_code, path)
    dct[f"{path}|value"] = model.value
    return dct


@flat.register
def _flat_party_identified(model: PartyIdentified, path: str) -> Dict:
    return {f"{path.strip('/')}|name": model.name}


@flat.register
def _flat_null_flavour(model: NullFlavour, path: str) -> Dict:
    _flat = {}
    _flat[f"{path}/_null_flavour|value"] = model.value
    _flat[f"{path}/_null_flavour|code"] = model.code
    _flat[f"{path}/_null_flavour|terminology"] = model.terminology

    _flat[path] = model.place_holder
    return _flat


def diff(flat_1: Dict, flat_2: Dict):
    return DeepDiff(flat_1, flat_2, verbose_level=2)
