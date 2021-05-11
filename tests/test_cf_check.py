import os

from pywps import Service
from pywps.tests import client_for, assert_response_success, assert_process_exception

from .common import get_output, PYWPS_CFG, MINI_CEDA_CACHE_DIR
from vulture.processes.wps_cf_check import CFCheck

import pytest
import xml.etree.ElementTree as ET

TEST_FILES = [
    os.path.join(MINI_CEDA_CACHE_DIR, 'main/archive/badc/cru/data/cru_ts/cru_ts_4.04/data/tmp/cru_ts4.04.1901.2019.tmp.dat.nc')
]


def test_cf_check(load_ceda_test_data):
    client = client_for(Service(processes=[CFCheck()], cfgfiles=[PYWPS_CFG]))
    nc_path = TEST_FILES[0]

    datainputs = f"cf_version=auto;nc_file_path={nc_path}"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=CFCheck&datainputs={datainputs}"
    )
    assert_response_success(resp)

    output_file = get_output(resp.xml)["output"][7:] #trim off 'file://'
    output = open(output_file).read()

    assert output.startswith('CHECKING NetCDF FILE:')
    assert 'Checking variable: lat' in output
    assert "INFO: Invalid Type for attribute: _FillValue <class 'numpy.float32'>" in output
    assert 'ERRORS detected: 0' in output
    assert 'WARNINGS given: 0'
    assert 'INFORMATION messages: 2'

