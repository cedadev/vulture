import os

from pywps import Service
from pywps.tests import client_for, assert_response_success, assert_process_exception

from .common import get_output, PYWPS_CFG, MINI_CEDA_CACHE_DIR
from vulture.processes.wps_amof_comp_check import AMOFCompCheck

import pytest
import xml.etree.ElementTree as ET

TEST_FILES = [
    os.path.join(MINI_CEDA_CACHE_DIR, 'main/archive/badc/cru/data/cru_ts/cru_ts_4.04/data/tmp/cru_ts4.04.1901.2019.tmp.dat.nc')
]

BAD_FILE = os.path.join(MINI_CEDA_CACHE_DIR, 'main/archive/badc/ukmo-midas/data/TD/yearly_files/midas_tmpdrnl_201901-201912.txt')

TEST_URLS = [
    'https://www.unidata.ucar.edu/software/netcdf/examples/tos_O1_2001-2002.nc'
]


def test_amof_comp_check_FilePath_success(load_ceda_test_data):
    client = client_for(Service(processes=[AMOFCompCheck()], cfgfiles=[PYWPS_CFG]))
    file_path = TEST_FILES[0]

    datainputs = f"AMOFChecksVersion=auto;FilePath={file_path}"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=AMOFCompCheck&datainputs={datainputs}"
    )
    assert_response_success(resp)

    output_file = get_output(resp.xml)["output"][7:] # trims off 'file://'
    output = open(output_file).read()

    assert "IOOS Compliance Checker Report" in output


def UPDATE_ME_test_cf_check_NetCDFFilePath_fail_no_file():
    client = client_for(Service(processes=[CFCheck()], cfgfiles=[PYWPS_CFG]))

    datainputs = f"cf_version=auto;NetCDFFilePath=RUBBISH"

    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=CFCheck&datainputs={datainputs}"
    )

    resp_str = resp.response[0].decode('utf-8')
    assert "Process error: Could not run CF-Checker on input file" in resp_str
    assert "ExceptionReport" in resp_str


def UPDATE_ME_test_cf_check_NetCDFFilePath_fail_bad_file():
    client = client_for(Service(processes=[CFCheck()], cfgfiles=[PYWPS_CFG]))

    datainputs = f"cf_version=auto;NetCDFFilePath={BAD_FILE}"

    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=CFCheck&datainputs={datainputs}"
    )

    resp_str = resp.response[0].decode('utf-8')
    assert "Process error: Could not run CF-Checker on input file" in resp_str


def UPDATE_ME_test_cf_check_NetCDFFileUpload_success():
    client = client_for(Service(processes=[CFCheck()], cfgfiles=[PYWPS_CFG]))
    nc_url = TEST_URLS[0]

    datainputs = f"cf_version=auto;NetCDFFileURL={nc_url}"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=CFCheck&datainputs={datainputs}"
    )
    assert_response_success(resp)

    output_file = get_output(resp.xml)["output"][7:] # trims off 'file://'
    output = open(output_file).read()

    assert output.startswith('CHECKING NetCDF FILE:')
    assert 'Checking variable: lat' in output
    assert 'ERRORS detected: 0' in output
    assert 'WARNINGS given: 1'
    assert 'INFORMATION messages: 0'

