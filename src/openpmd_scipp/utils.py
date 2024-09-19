import scipp as sc
import numpy as np
def _unit_dimension_to_scipp(unit_dimension):
    # unit dimension description from the openPMD standard:
    # powers of the 7 base measures characterizing the record's unit in SI
    # (length L, mass M, time T, electric current I, thermodynamic temperature theta,
    # amount of substance N, luminous intensity J)
    base_units = (
        1.0 * sc.Unit('m'),
        1.0 * sc.Unit('kg'),
        1.0 * sc.Unit('s'),
        1.0 * sc.Unit('A'),
        1.0 * sc.Unit('K'),
        1.0 * sc.Unit('mol'),
        1.0 * sc.Unit('cd'),
    )
    unit = 1.0 * sc.Unit('1')
    for dim, base_unit in zip(unit_dimension, base_units):
        if dim != 0:
            unit *= base_unit**dim
    return unit.unit

def closest(data, dim, val):
    val = val.astype('double')
    coord = data.coords[dim]
    val = val.to(unit=coord.unit)
    return np.argmin(sc.abs(coord - val).values)
