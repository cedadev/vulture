import os
from collections import namedtuple

from netCDF4 import Dataset

from .common import MINI_CEDA_CACHE_DIR

from vulture.utils import resolve_conventions_version


_i = namedtuple("_i", "data") 


TEST_FILE = os.path.join(MINI_CEDA_CACHE_DIR, 
            'main/archive/badc/cru/data/cru_ts/cru_ts_4.04/data/tmp/cru_ts4.04.1901.2019.tmp.dat.nc')


def _dummy(value):
    return {"CFVersion": [_i(value)]} 


def test_resolve_conventions_version(load_ceda_test_data):
    inputs = _dummy("auto")
    res = resolve_conventions_version(inputs, None)
    assert res.tuple == (1, 7)

    inputs = _dummy("rubbish")
    res = resolve_conventions_version(inputs, None)
    assert res.tuple == (1, 7)

    inputs = _dummy("auto")
    res = resolve_conventions_version(inputs, TEST_FILE)
    assert res.tuple == (1, 4)


def _write_ds_with_conv(nc_file, conv):
    ds = Dataset(nc_file, 'w', format="NETCDF4")
    dim = ds.createDimension('dim', 1)
    v = ds.createVariable("var","i4", ("dim",))

    v[:] = [3]
    ds.setncattr("Conventions", "AMOF-1.0, CF-1.5")
    ds.close()


def test_resolve_conventions_version_complex_string(tmp_path):
    inputs = _dummy("auto")
    nc_file = os.path.join(tmp_path, "complex_conv.nc")

    for conv in ("AMOF-1.0, CF-1.5", "AMOF-1.0; CF-1.5", "CF-1.5,OTHER-2.2.2,OK-5.5"):

        _write_ds_with_conv(nc_file, conv) 
        res = resolve_conventions_version(inputs, nc_file)
        assert res.tuple == (1, 5) 

   
