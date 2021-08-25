import requests
from requests.auth import HTTPBasicAuth


class Auth:
    ...


class Response(requests.Response):
    ...


def post(address, json, auth: Auth = None, headers=None) -> Response:
    return requests.post(address, json=json, auth=auth, headers=headers)


def get(address, params=None, auth: Auth = None, headers=None) -> Response:
    return requests.get(address, params=params, auth=auth, headers=headers)


class BasicAuth(Auth, HTTPBasicAuth):
    def __init__(self, user, password):
        HTTPBasicAuth.__init__(self, user, password)
