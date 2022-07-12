import logging
from dataclasses import dataclass
from typing import Dict, Optional, cast
from uuid import uuid4

import requests
from requests.auth import HTTPBasicAuth, AuthBase

from flatehr.core import Composition

logger = logging.getLogger()


def post(address, json, auth: Optional["Auth"], headers=None) -> "Response":
    resp = requests.post(address, json=json, auth=auth, headers=headers)
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as ex:
        raise HTTPException(resp.text, ex.args) from ex
    return cast(Response, resp)


def get(
    address, params=None, auth: Optional["Auth"] = None, headers=None
) -> "Response":
    resp = requests.get(address, params=params, auth=auth, headers=headers)
    return cast(Response, resp)


class Auth(AuthBase):
    ...


class BasicAuth(Auth, HTTPBasicAuth):
    def __init__(self, user, password):
        HTTPBasicAuth.__init__(self, user, password)


class Response(requests.Response):
    ...


class HTTPException(Exception):
    def __init__(self, text: str, *args):
        self.text = text
        super().__init__(*args)

    def __str__(self):
        return self.text


@dataclass
class OpenEHRClient:
    address: str
    auth: Optional[Auth] = None
    dry_run: bool = False
    _composition_base_path: str = "ehrbase/rest/ecis/v1/composition"

    def post_composition(self, composition: Composition, ehr_id: str) -> str:
        if not self.dry_run:
            # @fixme how template id is retrieved
            template_id = composition.web_template.path.strip("/")
            resp = post(
                f"{self.address}/{self._composition_base_path}?format=FLAT&ehrId={ehr_id}&templateId={template_id}",
                composition.as_flat(),
                self.auth,
                headers={"Prefer": "return=representation"},
            )

            resp_json = resp.json()
            return resp_json["compositionUid"]
        return ""

    def get_composition(self, composition_id: str) -> Dict:
        if self.dry_run:
            return {}
        resp = get(
            f"{self.address}/{self._composition_base_path}/{composition_id}",
            params={"format": "FLAT"},
            auth=self.auth,
        )
        resp.raise_for_status()
        return resp.json()["composition"]

    def create_ehr(self, _id: str = None) -> str:
        _id = _id or str(uuid4())
        if not self.dry_run:
            user_data = {
                "_type": "EHR_STATUS",
                "archetype_node_id": "openEHR-EHR-EHR_STATUS.generic.v1",
                "name": {"value": "EHR Status"},
                "subject": {
                    "external_ref": {
                        "id": {
                            "_type": "GENERIC_ID",
                            "value": _id,
                            "scheme": "id_scheme",
                        },
                        "namespace": "examples",
                        "type": "PERSON",
                    }
                },
                "is_modifiable": True,
                "is_queryable": True,
            }
            resp = post(
                f"{self.address}/ehrbase/rest/openehr/v1/ehr",
                json=user_data,
                auth=self.auth,
                headers={"Prefer": "return=representation"},
            )
            ehr_id = resp.json()["ehr_id"]["value"]
            logger.debug("created ehr_id %s", ehr_id)
            return ehr_id
        return _id
