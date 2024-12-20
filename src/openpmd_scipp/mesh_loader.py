import openpmd_api as pmd
import scipp as sc
import numpy as np
from dataclasses import dataclass
from copy import copy

from .utils import _unit_dimension_to_scipp


class DataRelay(sc.DataArray):

    def _verify_init(self):
        for dim in self.dims:
            coord = self.coords[dim]
            diffs = coord[dim, 1:] - coord[dim, :-1]
            diffs = diffs.to(unit='m')
            idx = list(self.record.axis_labels).index(dim)
            step = self.record.grid_spacing[idx]
            step *= self.record.grid_unit_SI
            step = step * sc.Unit('m')
            assert sc.allclose(diffs, step), f"The data has to be contiguous! diffs: {diffs}, step: {step}"

    def __init__(self,series, record, record_component, dummy_array, coords):
        super().__init__(data=dummy_array, coords=coords)
        self.series= series
        self.record =record
        self.record_component=record_component
        self._verify_init()

    def __getitem__(self, *args, **kwargs):
        dummy_data_aray = super().__getitem__(*args, **kwargs)
        return DataRelay(series=self.series, record=self.record,
                         record_component=self.record_component,
                         dummy_array=dummy_data_aray.data, coords=dummy_data_aray.coords)

    def load_data(self):
        offset = [0] * self.record_component.ndim
        extent = [0] * self.record_component.ndim
        for dd, dim in enumerate(self.record.axis_labels):
            try:
                start = self.coords[dim].to(unit='m').value
            except sc.DimensionError:
                start = self.coords[dim][0].to(unit='m').value
            start /= self.record.grid_unit_SI
            start -= self.record.grid_global_offset[dd]
            start /= self.record.grid_spacing[dd]
            start -= self.record_component.position[dd]
            offset[dd] = int(round(start))
            extent[dd] = self.coords[dim].size
        data = self.record_component.load_chunk(offset=offset, extent=extent)
        self.series.flush()
        data *= self.record_component.unit_SI
        data = np.squeeze(data)
        self.values = data
        return self


def get_field_data_relay(series, iteration,
                         field,
                         component=pmd.Mesh_Record_Component.SCALAR):
    record = series.iterations[iteration].meshes[field]
    rc = record[component]
    dims = record.axis_labels
    time = (series.iterations[iteration].time + record.time_offset) * series.iterations[iteration].time_unit_SI
    time = sc.scalar(time, unit='s', dtype='double')
    coords = {'t': time}
    for dd, dim in enumerate(dims):
        length = rc.shape[dd]
        start = record.grid_global_offset[dd]
        step =  record.grid_spacing[dd]
        values = np.arange(length, dtype=np.float64)
        values *= step
        values += rc.position[dd] * step
        values += start
        values *= record.grid_unit_SI
        coord = sc.array(dims=[dim], values=values, unit='m')
        coords[dim] = coord

    small = np.zeros(1, dtype=rc.dtype)
    dummy_array = np.lib.stride_tricks.as_strided(small, shape=rc.shape, strides=[0] * rc.ndim,
                                                  writeable=False)
    dummy_array = sc.array(dims=dims, values=dummy_array,
                           unit=_unit_dimension_to_scipp(record.unit_dimension))


    return DataRelay(series=series, record=record, record_component=rc, dummy_array=dummy_array, coords=coords)


def get_field(series, iteration,
              field,
              component=pmd.Mesh_Record_Component.SCALAR):
    return get_field_data_relay(series, iteration, field, component).load_data()
