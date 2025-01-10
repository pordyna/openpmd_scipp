"""
openpmd_scipp: A Python package for loading openPMD datasets into scipp DataArrays.


Modules:
    - mypackage.loader: Functions to load datasets from various sources.
    - mypackage.transform: Data transformation functions (e.g., filtering, aggregation).
    - mypackage.visualize: Functions for creating data visualizations and reports.

Installation:
    Install this package via pip:
        pip install mypackage

Usage:
    Example usage of the package:

    import mypackage

    # Load a dataset
    data = mypackage.load.load_data('data.csv')

    # Perform data transformation
    transformed_data = mypackage.transform.filter_data(data)

    # Generate a report
    mypackage.visualize.create_report(transformed_data)

Author:
    Your Name <your.email@example.com>

License:
GPL - 3.0 license. See LICENSE file for details.
"""
from .utils import closest as closest
from .loader import DataLoader as DataLoader
