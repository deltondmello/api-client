"""
A dummy api has been setup with the below ORG_ID and node type

Top Company
├── Edinburgh
│   └── Edinburgh Office
└── Montreal
    └── Montreal Office

Where Edinburgh and Montreal have been assumed to be divisions and Edinburgh Office
and Montreal Office as sites and Top Company at the top to be the root

NOTE
This script was written to be compatiable running with Django settings and models
"""

import json
from typing import Optional
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.cache import cache


LOCAL_HIERARCHY_URL = "https://platform-hierarchy-service.localhost.net/"
ORG_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
HIERARCHY_TYPE = "location"


def get_access_token():

    token = cache.get("access_token")

    if token:
        return token

    url = urljoin(settings.AUTH_URL, "/oauth/token")

    data = {
        "client_id": settings.AUTH_CLIENT_ID,
        "client_secret": settings.AUTH_CLIENT_SECRET,
        "audience": settings.AUTH_AUDIENCE_ID,
        "grant_type": "client_credentials",
    }

    response = requests.post(url, data=data)

    response.raise_for_status()

    if response.ok:
        response_json = response.json()
        token_type = response_json.get("token_type")
        access_token = response_json.get("access_token")
        expiry = response_json.get("expires_in")
        cache.set("access_token", f"{token_type} {access_token}", expiry)

        return f"{token_type} {access_token}"

    return None


def make_api_call(method, uri, payload={}, uri_params={}):

    token = get_access_token()

    url = urljoin(LOCAL_HIERARCHY_URL, uri)

    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "accept": "application/json",
    }

    response = requests.request(
        method, url, params=uri_params, data=payload, headers=headers
    )

    response.raise_for_status()

    print(f"Positive Response - {response.ok}")
    print(f"Hierarchy response status code - {response.status_code}")

    return response


# INSERTS


def insert_root_companyunit_node():
    uri = f"/v1/organisation/{ORG_ID}/hierarchy/{HIERARCHY_TYPE}"
    payload = json.dumps(
        {
            "shortCode": "root",
            "name": "Top Company",
            "archived": False,
            "nodeType": "company",
        }
    )

    make_api_call("PUT", uri, payload=payload)


def insert_company_unit_division_node():
    shortCode = "edinburgh"
    uri = f"/v1/organisation/{ORG_ID}/hierarchy/{HIERARCHY_TYPE}/nodes/{shortCode}"

    payload = json.dumps(
        {
            "name": "Edinburgh",
            "parentShortCode": "root",
            "parentId": "40c46fec-206e-426b-8c6c-199925c44441",
            "archived": False,
            "nodeType": "division",
        }
    )

    make_api_call("PUT", uri, payload=payload)


def insert_company_unit_site_node():
    shortCode = "eedinburgh-office"
    uri = f"/v1/organisation/{ORG_ID}/hierarchy/{HIERARCHY_TYPE}/nodes/{shortCode}"

    payload = json.dumps(
        {
            "name": "Edinburgh Office",
            "parentShortCode": "edinburgh",
            "parentId": "caa8aae2-ab54-4f0d-a580-28e1ce49cc60",
            "archived": False,
            "nodeType": "site",
        }
    )

    make_api_call("PUT", uri, payload=payload)


def get_root_companyunit_node():
    uri = f"/v1/organisation/{ORG_ID}/hierarchy/{HIERARCHY_TYPE}/nodes"
    params = {"$filter": "ShortCode eq 'root'"}
    return make_api_call("GET", uri, uri_params=params)


def get_company_unit_node(nodeId: str):
    """
    Get info on a specific node

    :param nodeId: used to query info about specified node
    """
    uri = f"/v1/organisation/{ORG_ID}/hierarchy/{HIERARCHY_TYPE}/nodes/{nodeId}"

    return make_api_call("GET", uri)


def get_divisions_company_unit_nodes():
    uri = f"/v1/organisation/{ORG_ID}/hierarchy/{HIERARCHY_TYPE}/nodes"
    params = {
        "$filter": "NodeType eq 'division'"
    }

    return make_api_call("GET", uri, uri_params=params)


def get_sites_company_unit_nodes():
    uri = f"/v1/organisation/{ORG_ID}/hierarchy/{HIERARCHY_TYPE}/nodes"
    params = {
        "$filter": "NodeType eq 'site'"
    }

    return make_api_call("GET", uri, uri_params=params)


def get_company_unit_nodes():
    """
    Gets all nodes except the root node
    """

    uri = f"/v1/organisation/{ORG_ID}/hierarchy/{HIERARCHY_TYPE}/nodes"

    params = {"$filter": "ShortCode ne 'root'"}

    return make_api_call("GET", uri, uri_params=params)


# ARCHIVES


def archive_company_unit_node(nodeId: str):
    uri = f"/v1/organisation/{ORG_ID}/hierarchy/{HIERARCHY_TYPE}/nodes/{nodeId}"

    payload = json.dumps(
        [
            {"value": True, "path": "/Archived", "op": "replace"},
        ]
    )

    make_api_call("PATCH", uri, payload=payload)


def unarchive_company_unit_node(nodeId: str):
    uri = f"/v1/organisation/{ORG_ID}/hierarchy/{HIERARCHY_TYPE}/nodes/{nodeId}"

    payload = json.dumps(
        [
            {"value": False, "path": "/Archived", "op": "replace"},
        ]
    )

    make_api_call("PATCH", uri, payload=payload)


# UTILS


def _get_root_value(json_payload: dict) -> Optional[dict]:
    try:
        return json_payload["value"][0]
    except KeyError as e:
        print(f"Error occurred when getting root payload value {e}")


def _get_root_id(json_payload: dict):

    try:
        return json_payload["value"][0]["Id"]
    except KeyError as e:
        print(f"Error occurred when getting root id {e}")


def _get_all_node_values(json_payload: dict):
    return [val for val in json_payload["value"]]


##
# Trigger API calls
##

def main():
    root_resp = get_root_companyunit_node()
    division_nodes = get_divisions_company_unit_nodes()
    site_nodes = get_sites_company_unit_nodes()

    root_value = _get_root_value(root_resp.json())
    division_values = _get_all_node_values(division_nodes.json())
    site_values = _get_all_node_values(site_nodes.json())


if __name__ == "__main__":
    main()
