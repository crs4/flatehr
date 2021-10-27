from typing import Dict

import requests
from requests.auth import HTTPBasicAuth


def post(address, json, auth: "Auth" = None, headers=None) -> "Response":
    resp = requests.post(address, json=json, auth=auth, headers=headers)
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as ex:
        raise HTTPException(resp.text, ex.args) from ex
    return resp


def get(address, params=None, auth: "Auth" = None, headers=None) -> "Response":
    return requests.get(address, params=params, auth=auth, headers=headers)


class Auth:
    ...


class BasicAuth(Auth, HTTPBasicAuth):
    def __init__(self, user, password):
        HTTPBasicAuth.__init__(self, user, password)


class Response(requests.Response):
    ...


class HTTPException(Exception):
    def __init__(self, json: Dict, *args):
        self.json = json
        super().__init__(*args)
