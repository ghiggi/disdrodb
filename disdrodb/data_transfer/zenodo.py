#!/usr/bin/env python3

# -----------------------------------------------------------------------------.
# Copyright (c) 2021-2023 DISDRODB developers
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------.
"""DISDRODB Zenodo utility."""

import json
import os
from typing import List, Tuple

import requests

from disdrodb.configs import get_zenodo_token
from disdrodb.utils.compression import archive_station_data
from disdrodb.utils.yaml import read_yaml, write_yaml


def _check_http_response(
    response: requests.Response,
    expected_status_code: int,
    task_description: str,
) -> None:
    """Check the Zenodo HTTP request response status code and raise an error if not the expected one."""

    if response.status_code == expected_status_code:
        return

    error_message = f"Error {task_description}: {response.status_code}"
    data = response.json()

    if "message" in data:
        error_message += f" {data['message']}"

    if "errors" in data:
        for sub_data in data["errors"]:
            error_message += f"\n- {sub_data['field']}: {sub_data['message']}"

    raise ValueError(error_message)


def _create_zenodo_deposition(sandbox) -> Tuple[int, str]:
    """Create a new Zenodo deposition and get the deposit information.

    At every function call, the deposit_id and bucket url will change !

    Parameters
    ----------
    sandbox : bool
        If True, create the deposit on Zenodo Sandbox for testing purposes.
        If False, create the deposit on Zenodo.

    Returns
    -------
    deposit_id, bucket_url : Tuple[int, str]
        Zenodo deposition ID and bucket URL.

    """
    access_token = get_zenodo_token(sandbox=sandbox)

    # Define Zenodo deposition url
    host = "sandbox.zenodo.org" if sandbox else "zenodo.org"
    deposit_url = f"https://{host}/api/deposit/depositions"

    # Create a new deposition
    # url = f"{deposit_url}?access_token={access_token}"
    params = {"access_token": access_token}
    headers = {"Content-Type": "application/json"}
    response = requests.post(deposit_url, params=params, json={}, headers=headers)
    _check_http_response(response, 201, task_description="Creation of Zenodo deposition")

    # Get deposition ID and bucket URL
    data = response.json()
    deposit_id = data["id"]
    bucket_url = data["links"]["bucket"]
    deposit_url = f"{deposit_url}/{deposit_id}"
    return deposit_id, deposit_url, bucket_url


def _upload_file_to_zenodo(file_path: str, metadata_fpath: str, sandbox: bool) -> None:
    """Upload a file to a Zenodo bucket."""

    # Read metadata
    metadata = read_yaml(metadata_fpath)
    data_source = metadata["data_source"]
    campaign_name = metadata["campaign_name"]

    # Define Zenodo bucket url
    deposit_id, deposit_url, bucket_url = _create_zenodo_deposition(sandbox=sandbox)

    # Define remote filename and remote url
    # --> <data_source>-<campaign_name>-<station_name>.zip !
    filename = os.path.basename(file_path)
    filename = f"{data_source}-{campaign_name}-{filename}"
    remote_url = f"{bucket_url}/{filename}"

    # Define access tokens
    access_token = get_zenodo_token(sandbox)
    params = {"access_token": access_token}

    ###----------------------------------------------------------.
    # Upload data
    with open(file_path, "rb") as f:
        response = requests.put(remote_url, data=f, params=params)
    host_name = "Zenodo Sandbox" if sandbox else "Zenodo"
    _check_http_response(response, 201, f"Upload of {file_path} to {host_name}.")

    ###----------------------------------------------------------.
    # Add zenodo metadata
    headers = {"Content-Type": "application/json"}
    zenodo_metadata = _define_zenodo_metadata(metadata)
    response = requests.put(deposit_url, params=params, data=json.dumps(zenodo_metadata), headers=headers)
    _check_http_response(response, 200, "Add Zenodo metadata deposit.")

    ###----------------------------------------------------------.
    # Define disdrodb data url
    zenodo_host = "sandbox.zenodo.org" if sandbox else "zenodo.org"
    disdrodb_data_url = f"https://{zenodo_host}/records/{deposit_id}/files/{filename}"
    disdrodb_data_url = f"https://{zenodo_host}/records/{deposit_id}/files/{filename}?download=1&preview=1"

    # Define Zenodo url to review and publish the uploaded data
    review_url = f"https://{zenodo_host}/uploads/{deposit_id}"

    ###----------------------------------------------------------.
    print(f"Please review your data deposition at {review_url} and publish it when ready !")
    print(f"The direct link to download station data is {disdrodb_data_url}")
    return disdrodb_data_url


def _define_creators_list(metadata):
    """Try to define Zenodo creator list from DISDRODB metadata."""
    try:
        import re

        list_names = re.split(";|,", metadata["authors"])
        list_identifier = re.split(";|,", metadata["authors_url"])
        list_affiliation = re.split(";|,", metadata["institution"])
        if len(list_names) != len(list_identifier):
            # print("Impossible to automatically assign identifier to authors. Length mismatch.")
            list_identifier = [""] * len(list_names)
        if len(list_affiliation) == 1:
            list_affiliation = list_affiliation * len(list_names)
        list_creator_dict = []
        for name, identifier, affiliation in zip(list_names, list_identifier, list_affiliation):
            creator_dict = {}
            creator_dict["name"] = name.strip()
            creator_dict["identifier"] = identifier.strip()
            creator_dict["affiliation"] = affiliation.strip()
            list_creator_dict.append(creator_dict)
    except Exception:
        list_creator_dict = []
    return list_creator_dict


def _define_zenodo_metadata(metadata):
    """Define Zenodo metadata from DISDRODB metadata."""
    data_source = metadata["data_source"]
    campaign_name = metadata["campaign_name"]
    station_name = metadata["station_name"]
    name = f"{data_source} {campaign_name} {station_name}"
    zenodo_metadata = {
        "metadata": {
            "title": f"{name} disdrometer station data",
            "upload_type": "dataset",
            "description": f"Disdrometer measurements of the {name} station",
            "creators": _define_creators_list(metadata),
        }
    }
    return zenodo_metadata


def _update_metadata_with_zenodo_url(metadata_fpath: str, disdrodb_data_url: str) -> None:
    """Update metadata with Zenodo zip file url.

    Parameters
    ----------
    metadata_fpath: str
        Metadata file path.
    disdrodb_data_url: str
        Remote URL where the station data are stored.
    """
    metadata_dict = read_yaml(metadata_fpath)
    metadata_dict["disdrodb_data_url"] = disdrodb_data_url
    write_yaml(metadata_dict, metadata_fpath)


def upload_station_to_zenodo(metadata_fpath: str, sandbox: bool = True) -> str:
    """Zip station data, upload data to Zenodo and update the metadata disdrodb_data_url.

    Parameters
    ----------
    metadata_fpath: str
        Metadata file path.
    sandbox: bool
        If True, upload to Zenodo Sandbox for testing purposes.
    """
    # Zip station data
    station_zip_fpath = archive_station_data(metadata_fpath)

    # Upload the station data zip file on Zenodo
    # - After upload, it removes the zip file !
    try:
        disdrodb_data_url = _upload_file_to_zenodo(
            file_path=station_zip_fpath, metadata_fpath=metadata_fpath, sandbox=sandbox
        )
        os.remove(station_zip_fpath)
    except Exception as e:
        os.remove(station_zip_fpath)
        raise ValueError(f"The upload on Zenodo has failed: {e}.")

    # Add the disdrodb_data_url information to the metadata
    _update_metadata_with_zenodo_url(metadata_fpath=metadata_fpath, disdrodb_data_url=disdrodb_data_url)


def upload_archive_to_zenodo(metadata_fpaths: List[str], sandbox: bool = True) -> None:
    """Upload data to Zenodo Sandbox.

    Parameters
    ----------
    metadata_fpaths: list of str
        List of metadata file paths.
    sandbox: bool
        If True, upload to Zenodo Sandbox for testing purposes.
    """
    for metadata_fpath in metadata_fpaths:
        try:
            # Upload station data
            upload_station_to_zenodo(metadata_fpath, sandbox=sandbox)
        except Exception as e:
            print(f"{e}")

    print("All data have been uploaded. Please review your data depositions and publish it when ready.")