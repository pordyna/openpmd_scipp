"""Test.

blalbla
"""

import scipp as sc
from memory_profiler import profile

import openpmd_scipp as pmdsc


@profile
def main():
    """Test."""
    path = "openPMD-example-datasets/example-3d/hdf5/data%T.h5"
    path = "../.data/" + path
    data_loader = pmdsc.DataLoader(path)

    # The full 3D array is not loaded into memory at this point.
    ex = data_loader.get_field("E", "x", time=sc.scalar(65.0, unit="fs"), relay=True)
    # This time we will select a range rather than a slice.
    # For a range there is no need for an exact match.
    # But, we could also select a slice just like in the previous example.
    # Ex = Ex["x", sc.scalar(-2e-6, unit="m"): sc.scalar(2e-6, unit="m")]
    # Only now the smaller subset wil be loaded into memory
    ex = ex.load_data()
    print(ex.size * 64 / 8 / 1024 / 1024)
    del data_loader.series


if __name__ == "__main__":
    main()
