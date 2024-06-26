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
from disdrodb.l0 import run_l0a
from disdrodb.l0.l0_reader import is_documented_by, reader_generic_docstring


@is_documented_by(reader_generic_docstring)
def reader(
    raw_dir,
    processed_dir,
    station_name,
    # Processing options
    force=False,
    verbose=False,
    parallel=False,
    debugging_mode=False,
):
    """Reader."""
    ##------------------------------------------------------------------------.
    #### - Define column names
    column_names = ["TO_PARSE"]

    ##------------------------------------------------------------------------.
    #### - Define reader options
    reader_kwargs = {}
    # - Define delimiter
    reader_kwargs["delimiter"] = "\\n"

    # Skip first row as columns names
    reader_kwargs["header"] = None

    # - Avoid first column to become df index !!!
    reader_kwargs["index_col"] = False

    # - Define behaviour when encountering bad lines
    reader_kwargs["on_bad_lines"] = "skip"

    # - Define encoding
    reader_kwargs["encoding"] = "ISO-8859-1"

    # - Define reader engine
    #   - C engine is faster
    #   - Python engine is more feature-complete
    reader_kwargs["engine"] = "python"

    # - Define on-the-fly decompression of on-disk data
    #   - Available: gzip, bz2, zip
    reader_kwargs["compression"] = "infer"

    # - Strings to recognize as NA/NaN and replace with standard NA flags
    #   - Already included: '#N/A', '#N/A N/A', '#NA', '-1.#IND', '-1.#QNAN',
    #                       '-NaN', '-nan', '1.#IND', '1.#QNAN', '<NA>', 'N/A',
    #                       'NA', 'NULL', 'NaN', 'n/a', 'nan', 'null'
    reader_kwargs["na_values"] = ["na", "", "error"]

    ##------------------------------------------------------------------------.
    #### - Define dataframe sanitizer function for L0 processing

    def df_sanitizer_fun(df):
        # - Import pandas
        import pandas as pd

        # - Retrieve file start time (date hour:minute)
        start_time = df["TO_PARSE"].iloc[0]
        start_time = start_time[0:16]
        start_time = pd.to_datetime(start_time, format="%m/%d/%Y %H:%M", errors="coerce")
        df = df.iloc[1:]  # remove start_time row

        # - Replace heterogeneous number of spaces with ;
        df["TO_PARSE"] = df["TO_PARSE"].str.replace(r" +", ";", regex=True)

        # - Split into columns and assign name
        df = df["TO_PARSE"].str.split(";", expand=True)
        columns = [
            "MMSSmmm",
            "rainfall_rate_32bit",
            "rainfall_accumulated_32bit",
            "reflectivity_32bit",
            "number_particles",
            "sensor_status",
            "error_code",
            "raw_drop_concentration",
            "raw_drop_average_velocity",
            "raw_drop_number",
        ]
        df.columns = columns

        # - Define datetime 'time' column
        dt_minute = df["MMSSmmm"].str[0:2].astype(int).astype("<m8[m]")
        dt_second = df["MMSSmmm"].str[2:4].astype(int).astype("<m8[s]")
        df_time = start_time + dt_minute + dt_second
        df["time"] = df_time

        # - Drop columns not agreeing with DISDRODB L0 standards
        df = df.drop(columns=["MMSSmmm"])

        return df

    ##------------------------------------------------------------------------.
    #### - Define glob pattern to search data files in <raw_dir>/data/<station_name>
    glob_patterns = "*.txt"

    ####----------------------------------------------------------------------.
    #### - Create L0A products
    run_l0a(
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        station_name=station_name,
        # Custom arguments of the reader for L0A processing
        glob_patterns=glob_patterns,
        column_names=column_names,
        reader_kwargs=reader_kwargs,
        df_sanitizer_fun=df_sanitizer_fun,
        # Processing options
        force=force,
        verbose=verbose,
        parallel=parallel,
        debugging_mode=debugging_mode,
    )
