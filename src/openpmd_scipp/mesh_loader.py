"""Module providing mesh like data loading capability.

Author:
    Pawel Ordyna <p.ordyna@hzdr.de>

License:
GPL - 3.0 license. See LICENSE file for details.
"""

from copy import deepcopy
from dataclasses import dataclass
from functools import cached_property
from types import EllipsisType
from typing import Iterable, MutableMapping

import numpy as np
import openpmd_api as pmd
import scipp as sc

from .utils import _unit_dimension_to_scipp

IndexingType = int | slice | sc.Variable | list[int]


@dataclass(frozen=True)
class DataRelay:
    """Data relay for loading openPMD meshes into scipp.

    Attributes
    ----------
    series : openpmd_api.Series
        The openPMD series object
    record : openpmd_api.Record
        The openPMD record object associated with the mesh
    record_component : openpmd_api.Record_Component
        The openPMD record component associated with the mesh

    Methods
    -------
    _verify_init():
        Ensures that the data range to load is contiguous.
    __getitem__(*args, **kwargs):
        Retrieves a subset of the data, returning a new DataRelay instance.
    load_data():
        Loads data from the record component based on data array coordinates,
        adjusting for offsets and extents, and updates the DataArray values.

    """

    dims: Iterable[str]
    coords: sc.typing.MetaDataMap
    unit: str | sc.Unit | None
    series: pmd.Series
    record: pmd.Mesh
    record_component: pmd.Mesh_Record_Component

    def __post_init__(self):
        """Verify that the data is contiguous.

        Check if the chosen subset is contiguous in the openPMD storage by checking coordinate
        differences against the expected grid spacing.

        This is needed since openPMD does nto allow us to load strided chunks.
        """
        dims_set = set(self.dims)
        dims_list = list(dims_set)

        if not len(dims_set) == len(dims_list):
            raise ValueError(f"Dimension labels must be unique. Passed dims {list(self.dims)}.")
        if not dims_set.issubset(self.coords.keys()):
            raise ValueError(
                f"Coordinates must be provided for all dimensions. but {dims_set}"
                f" is not a subset of {list(self.coords.keys())}."
            )
        for coord in self.coords.values():
            assert coord.ndim in {0, 1}, "Only 1 dimensional or scalar coordinates are supported."

        for dim in self.dims:
            if self.coords[dim].ndim != 0:
                assert sc.islinspace(self.coords[dim]), "The data has to be contiguous!"

    @cached_property
    def _da_extended_coords(self) -> MutableMapping[str, sc.DataArray]:
        """TODO."""
        return {
            k: sc.DataArray(data=v, coords={k: v}) for k, v in self.coords.items() if v.ndim >= 1
        }

    @cached_property
    def ndim(self) -> int:
        """TODO."""
        return len(list(self.dims))

    @cached_property
    def shape(self) -> tuple:
        """TODO."""
        return tuple([self.coords[k].size for k in self.dims])

    @cached_property
    def size(self) -> int:
        """TODO."""
        s = 1
        for ss in self.shape:
            s *= ss
        return s

    @cached_property
    def dtype(self) -> sc.typing.DTypeLike:
        """TODO."""
        return self.record_component.dtype

    def __getitem__(self, arg: EllipsisType | IndexingType | tuple[str, IndexingType]):
        """Retrieve a subset of the data, returning a new DataRelay instance.

        Override this method from the base class to use the DataRelay initializer and ensure that
        DataRelay is returned and the _verify_init method is used.

        :param args: Forwarded to the base class.
        :type args: tuple
        :param kwargs: Forwarded to the base class.
        :type kwargs: dict
        :return: A new DataRelay instance with the sliced data.
        :rtype: DataRelay
        """
        if arg is ...:
            return self

        if isinstance(arg, tuple):
            coord_str, arg = arg
        elif self.ndim == 1:
            coord_str = next(iter(self.dims))
        elif self.ndim == 0:
            raise ValueError("Can't slice a 0 dimensional Variable.")
        else:
            raise ValueError(
                "For ndim>1, one needs to choose a dimension to slice "
                "like: relay_instance['coord_label', <index, slice, etc..>]."
            )

        if coord_str not in self.dims:
            raise ValueError(f"{coord_str} not in dims: {list(self.dims)}.")
        # We do a deep copy, coordinate arrays are rather not that big, this is saver
        # but could probably think of sth else
        # We need coords as data arrays for indexing with sc.Variable
        new_coords = deepcopy(self._da_extended_coords)
        new_coords[coord_str] = new_coords[coord_str][(coord_str, arg)]
        # get back to normal coords containing Variables not DataArrays
        new_coords = {k: v.data for k, v in new_coords.items()}
        # keep scalar coords that are ignored in da_extended
        new_coords = dict(self.coords) | new_coords

        return DataRelay(
            series=self.series,
            record=self.record,
            record_component=self.record_component,
            dims=self.dims,
            unit=self.unit,
            coords=new_coords,
        )

    def load_data(self) -> sc.DataArray:
        """Load data from the openPMD dataset.

        Loads a chunk based on the current data array coordinates.

        Calculates the offset and extent for each dimension using the data array coordinates. Loads
        the data chunk from the record component, scales it by the unit SI, and returns a new data
        array with loaded values.

        :return: The DataArray instance with the loaded data.
        :rtype: DataRelay
        """
        offset = [0] * self.record_component.ndim
        extent = [0] * self.record_component.ndim
        for dd, dim in enumerate(self.record.axis_labels):
            try:
                start = self.coords[dim].to(unit="m").value
            except sc.DimensionError:
                start = self.coords[dim][0].to(unit="m").value
            start /= self.record.grid_unit_SI
            start -= self.record.grid_global_offset[dd]
            start /= self.record.grid_spacing[dd]
            start -= self.record_component.position[dd]
            offset[dd] = int(round(start))
            extent[dd] = self.coords[dim].size

        scipp_array = sc.empty(
            dims=tuple(self.dims), shape=self.shape, dtype=self.dtype, unit=self.unit
        )
        self.record_component.load_chunk(scipp_array.values.data, offset=offset, extent=extent)
        self.series.flush()
        scipp_array *= self.record_component.unit_SI
        scipp_array = sc.squeeze(scipp_array)
        data_array = sc.DataArray(data=scipp_array, coords=self.coords)
        return data_array


def get_field_data_relay(series, iteration, field, component=pmd.Mesh_Record_Component.SCALAR):
    """Get openPMD mesh as a data relay.

    Create a DataRelay object for a specified field and component in an openPMD series.

    :param series: The openPMD series containing the data.
    :type series: openpmd_api.Series
    :param iteration: The iteration number to access within the series.
    :type iteration: int
    :param field: The name of the field to retrieve.
    :type field: str
    :param component: The component of the field to retrieve, default is SCALAR.
    :type component: openpmd_api.Mesh_Record_Component, optional
    :return: A DataRelay instance initialized with the specified field and component data.
    :rtype: DataRelay
    """
    record = series.iterations[iteration].meshes[field]
    rc = record[component]
    dims = record.axis_labels
    time = (series.iterations[iteration].time + record.time_offset) * series.iterations[
        iteration
    ].time_unit_SI
    time = sc.scalar(time, unit="s", dtype="double")
    coords = {"t": time}
    for dd, dim in enumerate(dims):
        length = rc.shape[dd]
        start = record.grid_global_offset[dd]
        step = record.grid_spacing[dd]
        values = np.arange(length, dtype=np.float64)
        values *= step
        values += rc.position[dd] * step
        values += start
        values *= record.grid_unit_SI
        coord = sc.array(dims=[dim], values=values, unit="m")
        coords[dim] = coord

    unit = _unit_dimension_to_scipp(record.unit_dimension)
    return DataRelay(
        series=series, record=record, record_component=rc, dims=dims, coords=coords, unit=unit
    )


def get_field(series, iteration, field, component=pmd.Mesh_Record_Component.SCALAR):
    """Retrieve and load openPMD mesh data without slicing.

    This function creates a DataRelay object for a specified field and component in an openPMD
    series, loads the whole mesh, and returns the resulting DataArray.

    :param series: The openPMD series containing the data.
    :type series: openpmd_api.Series
    :param iteration: The iteration number to access within the series.
    :type iteration: int
    :param field: The name of the field to retrieve.
    :type field: str
    :param component: The component of the field to retrieve, default is SCALAR.
    :type component: openpmd_api.Mesh_Record_Component, optional
    :return: A DataArray instance with the loaded data.
    :rtype: DataRelay
    """
    return get_field_data_relay(series, iteration, field, component).load_data()
