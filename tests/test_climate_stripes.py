import os

#from pywps import Service
#from pywps.tests import client_for, assert_response_success, assert_process_exception

#from .common import get_output, PYWPS_CFG, MINI_CEDA_CACHE_DIR
from vulture.stripes_lib.stripes import HadUKStripesRenderer

#import pytest
#import xml.etree.ElementTree as ET


def test_HadUKStripesMaker():
    stripes_maker = HadUKStripesRenderer()

    outputs = {"pdf": "/tmp/output.pdf",
               "png": "/tmp/new-stripes2.png",
               "html": "/tmp/output.html"}

    # RAL_LAT, RAL_LON = 51.570664384, -1.308832098
    df = stripes_maker.create(51.570664384, -1.308832098, output_file=outputs["png"])
    html = stripes_maker.to_html(html_file=outputs["html"], project_name="My great project")
    pdf_file = stripes_maker.to_pdf(outputs["pdf"], project_name="Another project")
    #df = stripes_maker.create(51.23, -1.23, n_colours=10, cmap_name="winter", time_range=(1950, 2010), output_file="new-stripes.png")

    for f in outputs.values():
        assert os.path.isfile(f), f"{f} output file not found."
    #stripes_maker.show_table()
    #stripes_maker.show_table(full=False)
    #stripes_maker.show_plot()



