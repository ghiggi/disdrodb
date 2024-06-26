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
"""Define DISDRODB L0 readers routines."""

import logging
import os

logger = logging.getLogger(__name__)


####--------------------------------------------------------------------------.


def _get_readers_directory() -> str:
    """Returns the path to the ``disdrodb.l0.readers`` directory within the disdrodb package."""
    from disdrodb import __root_path__

    reader_dir = os.path.join(__root_path__, "disdrodb", "l0", "readers")
    return reader_dir


def _get_readers_data_sources() -> list:
    """Returns the readers data sources available at ``disdrodb.l0.readers``."""
    # Readers directory path
    reader_dir = _get_readers_directory()

    # List of readers directory
    list_data_sources = [os.path.basename(f.path) for f in os.scandir(reader_dir) if f.is_dir()]
    # Directory to remove
    bad_dirs = ["__pycache__", ".ipynb_checkpoints"]
    list_data_sources = [name for name in list_data_sources if name not in bad_dirs]

    return list_data_sources


def _get_readers_data_sources_path() -> list:
    """Returns the list of readers data sources directory paths within ``disdrodb.l0.readers``."""
    # Readers directory path
    reader_dir = _get_readers_directory()

    # List of readers directory
    list_data_sources = [f.path for f in os.scandir(reader_dir) if f.is_dir()]
    return list_data_sources


def _get_readers_paths_by_data_source(data_source):
    """Return the filepath list of available readers for a specific data source.

    This function does not check the ``data_source`` validity.
    """
    # Retrieve reader data source directory
    reader_dir = _get_readers_directory()
    reader_data_source_path = os.path.join(reader_dir, data_source)
    if not os.path.isdir(reader_data_source_path):
        raise ValueError(f"No {data_source} directory in disdrodb.l0.readers")
    # Retrieve list of available readers paths
    list_readers_paths = [f.path for f in os.scandir(reader_data_source_path) if f.is_file() and f.path.endswith(".py")]
    return list_readers_paths


def _get_readers_names_by_data_source(data_source):
    """Return the reader available for a given ``data_source``.

    This function does not check the ``data_source`` validity.
    """
    # Retrieve reader data source directory
    list_readers_paths = _get_readers_paths_by_data_source(data_source)
    list_readers_names = [os.path.basename(path).replace(".py", "") for path in list_readers_paths]
    return list_readers_names


####--------------------------------------------------------------------------.


def _check_reader_data_source(reader_data_source: str) -> str:
    """Check if the provided data source exists within the available readers.

    Please run ``_get_available_readers_dict()`` to get the list of all available reader.

    Parameters
    ----------
    reader_data_source : str
        The directory within which the ``reader_name`` is located in the
        ``disdrodb.l0.readers`` directory.

    Returns
    -------
    str
        If data source is valid, return the correct reader data source name.

    Raises
    ------
    ValueError
        Error if the data source name provided is not a directory within the ``disdrodb.l0.readers`` directory.
    """
    # List available readers data sources
    available_reader_data_sources = _get_readers_data_sources()
    # If not valid data_source, raise error
    if reader_data_source not in available_reader_data_sources:
        msg = f"Reader data source {reader_data_source} is not a directory inside the disdrodb.l0.readers directory."
        logger.error(msg)
        raise ValueError(msg)
    return reader_data_source


def _check_reader_exists(reader_data_source: str, reader_name: str) -> str:
    """Check if the provided data source exists and reader names exists within the available readers.

    Please run ``_get_available_readers_dict()`` to get the list of all available reader.

    Parameters
    ----------
    reader_data_source : str
        The directory within which the ``reader_name`` is located in the
        ``disdrodb.l0.readers`` directory.
    reader_name : str
        Campaign name

    Returns
    -------
    str
        If the reader exists, returns the ``reader_name``.
        If the reader does not exist, it raises a ValueError.

    Raises
    ------
    ValueError
        Error if the reader name provided for the campaign has not been found.
    """
    # Check valid data_source
    reader_data_source = _check_reader_data_source(reader_data_source)
    # Get available reader names
    list_readers_names = _get_readers_names_by_data_source(reader_data_source)
    # If not valid reader_name, raise error
    if reader_name not in list_readers_names:
        msg = f"Reader {reader_name} is not valid. Valid readers {list_readers_names}."
        logger.exception(msg)
        raise ValueError(msg)
    return reader_name


def _get_available_readers_dict() -> dict:
    """Returns the readers description included into the current release of DISDRODB.

    Returns
    -------
    dict
        The dictionary has the following schema ``{"data_source": {"reader_name": "reader_filepath"}}``.
    """
    # Format:
    # {data_source: {reader_name: reader_path,
    #                reader_name1: reader_path1}
    # }
    # Get list of reader data sources
    list_reader_data_sources = _get_readers_data_sources()

    # Build dictionary
    dict_reader = {}
    for data_source in list_reader_data_sources:
        # Retrieve the filepath of the available readers
        list_readers_paths = _get_readers_paths_by_data_source(data_source)
        # Initialize the data_source dictionary
        dict_reader[data_source] = {}
        for reader_path in list_readers_paths:
            reader_name = os.path.basename(reader_path).replace(".py", "")
            dict_reader[data_source][reader_name] = reader_path
    # Return available dictionary
    return dict_reader


def available_readers(data_sources=None, reader_path=False):
    """Retrieve available readers information."""
    # Get available readers dictionary
    dict_readers = _get_available_readers_dict()
    # If data sources is not None, subset the dictionary
    if data_sources is not None:
        # Check valid data sources
        if isinstance(data_sources, str):
            data_sources = [data_sources]
        data_sources = [_check_reader_data_source(data_source) for data_source in data_sources]
        # Create new dictionary
        dict_readers = {data_source: dict_readers[data_source] for data_source in data_sources}
    # If reader_path=False, provide {data_source: [list_reader_names]}
    if not reader_path:
        dict_readers = {data_source: list(dict_readers.keys()) for data_source, dict_readers in dict_readers.items()}
    return dict_readers


####--------------------------------------------------------------------------.


def get_reader_function(reader_data_source: str, reader_name: str) -> object:
    """Returns the reader function based on input parameters.

    Parameters
    ----------
    reader_data_source : str
        The directory within which the ``reader_name`` is located in the
        ``disdrodb.l0.readers directory``.
    reader_name : str
        The reader name.

    Returns
    -------
    object
        The ``reader()`` function

    """
    # Check data source and reader_name validity
    reader_data_source = _check_reader_data_source(reader_data_source)
    reader_name = _check_reader_exists(reader_data_source=reader_data_source, reader_name=reader_name)
    # Retrieve reader function
    if reader_name:
        full_name = f"disdrodb.l0.readers.{reader_data_source}.{reader_name}.reader"
        module_name, unit_name = full_name.rsplit(".", 1)
        my_reader = getattr(__import__(module_name, fromlist=[""]), unit_name)

    return my_reader


####--------------------------------------------------------------------------.
#### Checks for reader args


def _get_expected_reader_arguments():
    """Return a list with the expected reader arguments."""
    expected_arguments = [
        "raw_dir",
        "processed_dir",
        "station_name",
        "force",
        "verbose",
        "parallel",
        "debugging_mode",
    ]
    return expected_arguments


def _check_reader_arguments(reader):
    """Check the reader have the expected input arguments."""
    import inspect

    signature = inspect.signature(reader)
    reader_arguments = sorted(signature.parameters.keys())
    expected_arguments = sorted(_get_expected_reader_arguments())
    if reader_arguments != expected_arguments:
        raise ValueError(f"The reader must be defined with the following arguments: {expected_arguments}")


####--------------------------------------------------------------------------.
#### Checks for metadata reader key


def _check_metadata_reader(metadata):
    """Check the ``reader`` key is available and points to an existing disdrodb reader."""
    # Check the reader is specified
    if "reader" not in metadata:
        raise ValueError("The reader is not specified in the metadata.")
    # If the reader name is specified, test it is valid.
    # - Convention: reader: "<DATA_SOURCE>/<READER_NAME>" in disdrodb.l0.readers
    reader_reference = metadata.get("reader")
    # - Check it contains /
    if "/" not in reader_reference:
        raise ValueError(
            f"The reader '{reader_reference}' reported in the metadata is not valid. Must have"
            " '<DATA_SOURCE>/<READER_NAME>' pattern.",
        )
    # - Get the reader_reference component list
    reader_components = reader_reference.split("/")
    # - Check composed by two elements
    if len(reader_components) != 2:
        raise ValueError("Expecting the reader reference to be composed of <DATA_SOURCE>/<READER_NAME>.")
    # - Retrieve reader data source and reader name
    reader_data_source = reader_components[0]
    reader_name = reader_components[1]

    # - Check the reader is available
    _check_reader_exists(reader_data_source=reader_data_source, reader_name=reader_name)


def get_reader_function_from_metadata_key(reader_data_source_name):
    """Retrieve the reader function from the ``reader`` metadata value.

    The convention for metadata reader key: ``<data_source/reader_name>`` in ``disdrodb.l0.readers``.
    """
    reader_data_source = reader_data_source_name.split("/")[0]
    reader_name = reader_data_source_name.split("/")[1]
    reader = get_reader_function(reader_data_source=reader_data_source, reader_name=reader_name)
    return reader


def _get_reader_from_metadata(metadata):
    """Retrieve the reader function from the metadata key ``reader``.

    The convention for metadata reader key: ``<data_source/reader_name>`` in ``disdrodb.l0.readers``.
    """
    reader_data_source_name = metadata.get("reader")
    return get_reader_function_from_metadata_key(reader_data_source_name)


def get_station_reader_function(data_source, campaign_name, station_name, base_dir=None):
    """Retrieve the reader function from the station metadata."""
    from disdrodb.metadata import read_station_metadata

    # Get metadata
    metadata = read_station_metadata(
        base_dir=base_dir,
        product="RAW",
        data_source=data_source,
        campaign_name=campaign_name,
        station_name=station_name,
    )
    # ------------------------------------------------------------------------.
    # Check reader key is within the dictionary
    if "reader" not in metadata:
        raise ValueError(
            "The `reader` key is not available in the metadata of the"
            f" {data_source} {campaign_name} {station_name} station.",
        )

    # ------------------------------------------------------------------------.
    # Check reader name validity
    _check_metadata_reader(metadata)

    # ------------------------------------------------------------------------.
    # Retrieve reader
    reader = _get_reader_from_metadata(metadata)

    # ------------------------------------------------------------------------.
    # Check reader argument
    _check_reader_arguments(reader)

    return reader


####--------------------------------------------------------------------------.
#### Readers Docs


def is_documented_by(original):
    """Wrapper function to apply generic docstring to the decorated function.

    Parameters
    ----------
    original : function
        Function to take the docstring from.
    """

    def wrapper(target):
        target.__doc__ = original.__doc__
        return target

    return wrapper


def reader_generic_docstring():
    """Script to convert the raw data to L0A format.

    Parameters
    ----------
    raw_dir : str
        The directory path where all the raw content of a specific campaign is stored.
        The path must have the following structure ``<...>/DISDRODB/Raw/<DATA_SOURCE>/<CAMPAIGN_NAME>``.
        Inside the ``raw_dir`` directory, it is required to adopt the following structure::

            - ``/data/<station_name>/<raw_files>``
            - ``/metadata/<station_name>.yml``

        **Important points:**

        - For each ``<station_name>``, there must be a corresponding YAML file in the metadata subdirectory.
        - The ``<CAMPAIGN_NAME>`` are expected to be UPPER CASE.
        - The ``<CAMPAIGN_NAME>`` must semantically match between:

            - the ``raw_dir`` and ``processed_dir`` directory paths;
            - with the key ``campaign_name`` within the metadata YAML files.

    processed_dir : str
        The desired directory path for the processed DISDRODB L0A and L0B products.
        The path should have the following structure ``<...>/DISDRODB/Processed/<DATA_SOURCE>/<CAMPAIGN_NAME>``
        For testing purposes, this function exceptionally accepts also a directory path simply ending
        with ``<CAMPAIGN_NAME>`` (e.g., ``/tmp/<CAMPAIGN_NAME>``).

    station_name : str
        The name of the station.

    force : bool, optional
        If ``True``, overwrite existing data in destination directories.
        If ``False``, raise an error if data already exists in destination directories.
        Default is ``False``.

    verbose : bool, optional
        If ``True``, print detailed processing information to the terminal.
        Default is ``True``.

    parallel : bool, optional
        If ``True``, process the files simultaneously in multiple processes.
        The number of simultaneous processes can be customized using the ``dask.distributed.LocalCluster``.
        If ``False``, process the files sequentially in a single process.
        Default is ``False``.

    debugging_mode : bool, optional
        If ``True``, reduce the amount of data to process.
        Only the first 3 raw data files will be processed.
        Default is ``False``.
    """


####--------------------------------------------------------------------------.
#### Check DISDRODB readers


def check_available_readers():
    """Check the readers arguments of all package."""
    dict_all_readers = available_readers(data_sources=None, reader_path=False)
    for reader_data_source, list_reader_name in dict_all_readers.items():
        for reader_name in list_reader_name:
            try:
                reader = get_reader_function(reader_data_source=reader_data_source, reader_name=reader_name)
                _check_reader_arguments(reader)
            except Exception as e:
                raise ValueError(f"Invalid reader for {reader_data_source}/{reader_name}.py. The error is {e}")


####--------------------------------------------------------------------------.
