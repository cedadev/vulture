import os
from pathlib import Path

from pywps import get_ElementMakerForVersion
from pywps.app.basic import get_xpath_ns
from pywps.tests import WpsClient, WpsTestResponse

from jinja2 import Template
import tempfile

TESTS_HOME = os.path.abspath(os.path.dirname(__file__))
PYWPS_CFG = os.path.join(TESTS_HOME, "pywps.cfg")
ROOCS_CFG = os.path.join(tempfile.gettempdir(), "roocs.ini")

VERSION = "1.0.0"
WPS, OWS = get_ElementMakerForVersion(VERSION)
xpath_ns = get_xpath_ns(VERSION)

MINI_CEDA_CACHE_DIR = Path.home() / ".mini-ceda-archive"
MINI_CEDA_MASTER_DIR = os.path.join(MINI_CEDA_CACHE_DIR, "master")


def write_roocs_cfg():
    cfg_templ = """[project:cru_ts]
base_dir = {{ ceda_base_dir }}/archive/badc/cru/data/cru_ts
file_name_template = {__derive__var_id}_{frequency}_{__derive__time_range}.{__derive__extension}
fixed_path_mappings =
    cru_ts.4.04.cld:cru_ts_4.04/data/cld/*.nc
    cru_ts.4.04.dtr:cru_ts_4.04/data/dtr/*.nc
    cru_ts.4.04.frs:cru_ts_4.04/data/frs/*.nc
    cru_ts.4.04.pet:cru_ts_4.04/data/pet/*.nc
    cru_ts.4.04.pre:cru_ts_4.04/data/pre/*.nc
    cru_ts.4.04.tmn:cru_ts_4.04/data/tmn/*.nc
    cru_ts.4.04.tmp:cru_ts_4.04/data/tmp/*.nc
    cru_ts.4.04.tmx:cru_ts_4.04/data/tmx/*.nc
    cru_ts.4.04.vap:cru_ts_4.04/data/vap/*.nc
    cru_ts.4.04.wet:cru_ts_4.04/data/wet/*.nc
attr_defaults =
    frequency:mon
facet_rule = project version_major version_minor variable
    """

    cfg = Template(cfg_templ).render(ceda_base_dir=MINI_CEDA_MASTER_DIR)

    with open(ROOCS_CFG, "w") as fp:
        fp.write(cfg)

    # point to roocs cfg in environment
    os.environ["ROOCS_CONFIG"] = ROOCS_CFG


def resource_file(filepath):
    return os.path.join(TESTS_HOME, "testdata", filepath)


class WpsTestClient(WpsClient):
    def get(self, *args, **kwargs):
        query = "?"
        for key, value in kwargs.items():
            query += "{0}={1}&".format(key, value)
        return super(WpsTestClient, self).get(query)


def client_for(service):
    return WpsTestClient(service, WpsTestResponse)


def get_output(doc):
    """Copied from pywps/tests/test_execute.py.
    TODO: make this helper method public in pywps."""
    output = {}
    for output_el in xpath_ns(
        doc, "/wps:ExecuteResponse" "/wps:ProcessOutputs/wps:Output"
    ):
        [identifier_el] = xpath_ns(output_el, "./ows:Identifier")

        lit_el = xpath_ns(output_el, "./wps:Data/wps:LiteralData")
        if lit_el != []:
            output[identifier_el.text] = lit_el[0].text

        ref_el = xpath_ns(output_el, "./wps:Reference")
        if ref_el != []:
            output[identifier_el.text] = ref_el[0].attrib["href"]

        data_el = xpath_ns(output_el, "./wps:Data/wps:ComplexData")
        if data_el != []:
            output[identifier_el.text] = data_el[0].text

    return output
