from time import time_ns

import openpmd_api as pmd
import scipp as sc
from .mesh_loader import get_field, get_field_data_relay
from .utils import closest


def get_time_axis(series):
    t = [
        series.iterations[it].time * series.iterations[it].time_unit_SI for it in series.iterations
    ]
    return sc.array(dims=["t"], values=t, unit="s", dtype="double")


def get_iterations(series):
    t = get_time_axis(series)
    return sc.Dataset(
        data={
            "iteration_id": sc.DataArray(
                data=sc.array(dims=["t"], values=list(series.iterations)),
                coords={"t": t},
            )
        }
    )


class DataLoader:

    def __init__(self, path):
        self.series = pmd.Series(str(path), pmd.Access.read_only)
        self.iterations = get_iterations(self.series)

    def get_field(
        self,
        field,
        component=pmd.Mesh_Record_Component.SCALAR,
        time=None,
        iteration=None,
        relay=False,
        time_tolerance=10 * sc.Unit("fs"),
    ):
        assert (time is None and iteration is not None) or (
            iteration is None and time is not None
        ), "Provide either iteration index or time"
        if iteration is None:
            # handle integer  inputs
            time = time.astype("double")
            time_tolerance = time_tolerance.astype("double")
            time = time.to(unit=self.iterations["iteration_id"].coords["t"].unit)
            try:
                iteration = int(self.iterations["iteration_id"]["t", time].value)
            except IndexError:
                idx = closest(self.iterations["iteration_id"], "t", time)
                iteration = self.iterations["iteration_id"]["t", idx]
                assert time_tolerance is None or sc.abs(
                    iteration.coords["t"] - time
                ) <= time_tolerance.to(
                    unit=time.unit
                ), f"No iteration found within time_tolerance={time_tolerance}."
                print(
                    f"Series does not contain iteration at the exact time. Using closest iteration instead.",
                    flush=True,
                )
                iteration = int(iteration.value)

        if relay:
            return get_field_data_relay(
                series=self.series, field=field, component=component, iteration=iteration
            )
        else:
            return get_field(
                series=self.series, field=field, component=component, iteration=iteration
            )
