import os
import shutil
from pywps import (
    BoundingBoxInput,
    LiteralInput,
    Process,
    FORMATS,
    Format,
    ComplexOutput,
)

from pywps.app.Common import Metadata
from pywps.app.exceptions import ProcessError
from ..utils import get_input

from vulture.stripes_lib.stripes import HadUKStripesRenderer


import logging
LOGGER = logging.getLogger("PYWPS")


# Extend FORMATS
#FORMATS_EXT = FORMATS
#FORMATS_EXT.extend( [Format('application/pdf', extension='.pdf')])



class PlotClimateStripes(Process):

    IDENTIFIER = "PlotClimateStripes"
    TITLE = "Plot Climate Stripes"
    ABSTRACT = "Plots Climate Stripes...ad more text"
    KEYWORDS = ["climate", "observations", "change"]
    INPUTS_LIST = ["latitude", "longitude"]
    METALINK_ID = "plot-climate-stripes-result"

    PROCESS_METADATA = [
        Metadata("CEDA WPS UI", "https://ceda-wps-ui.ceda.ac.uk"),
        Metadata("CEDA WPS", "https://ceda-wps.ceda.ac.uk"),
        Metadata("Disclaimer", "https://help.ceda.ac.uk/article/4642-disclaimer"),
    ]

    def __init__(self):

        inputs = self._define_inputs()
        outputs = self._define_outputs()

        super(PlotClimateStripes, self).__init__(
            self._handler,
            identifier=self.IDENTIFIER,
            title=self.TITLE,
            abstract=self.ABSTRACT,
            keywords=self.KEYWORDS,
            metadata=self.PROCESS_METADATA,
            version="1.0.0",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True,
        )

    def _define_input(self, name, long_name, abstract, dtype="string", allowed_values=None, optional=False, default=None):
        return LiteralInput(
            name,
            long_name,
            abstract=abstract,
            data_type=dtype,
            allowed_values=allowed_values,
            min_occurs=(0 if optional else 1),
            max_occurs=1,
            default=default
        )

    def _define_inputs(self):
        inputs = [
            self._define_input("latitude", "Latitude", "Some text about Lat", "float"),
            self._define_input("longitude", "Longitude", "Some text about Lon", "float"),
            self._define_input("n_colours", "Number of colours", "Some text about ncols", "integer", default=20),
            self._define_input("project_name", "Project name", "A name for your project", "string", optional=True),
            self._define_input("start_year", "Start year", "Info about start year", "integer", default=1901),
            self._define_input("end_year", "End year", "Info about end year", "integer", default=2000)
            
#        LiteralInput( "yearNumericRange", "Time Period", abstract="The time period", data_type="string", default="1901/2000", min_occurs=1, max_occurs=1,)

        ] 
        return inputs

    def _define_outputs(self):
        outputs = [
            ComplexOutput('output', 'Output',
                          abstract='Output file',
                          as_reference=True,
                          supported_formats=[FORMATS.PDF])]
        return outputs


    def _handler(self, request, response):

        lat = get_input(request.inputs, "latitude")
        lon = get_input(request.inputs, "longitude")
        project_name = get_input(request.inputs, "project_name")
        n_colours = get_input(request.inputs, "n_colours")
        start_year = get_input(request.inputs, "start_year")
        end_year = get_input(request.inputs, "end_year")
    #    time_range = get_input(request.inputs, "yearNumericRange") 
   #     inputs = {"latitude": lat, "longitude": lon, "project_name": project_name}
   #     except Exception as exc:
   #        raise ProcessError(f"An error occurred when converting to CSV: {str(exc)}")

        png_file = os.path.join(self.workdir, "stripes.png")
        pdf_file = os.path.join(self.workdir, "stripes.pdf")
#        shutil.copy("/tmp/climate-stripes.png", output_file)

        # Make the stripes
        stripes_maker = HadUKStripesRenderer()
        response.update_status('Begin data loading', 10)

#        RAL = [51.570664384, -1.308832098]
        df = stripes_maker.create(lat, lon, n_colours=n_colours, output_file=png_file, time_range=(start_year, end_year))

        response.update_status('Data extracted', 70)

#        html = stripes_maker.to_html(html_file="/tmp/output.html", project_name="My great project")
        pdf_file_ = stripes_maker.to_pdf(pdf_file, project_name=project_name)
                
        response.update_status('Outputs written', 90)

        LOGGER.info(f'Written output file: {pdf_file}')
        response.outputs['output'].file = pdf_file
#        response.outputs['png_output'].file = png_file
        return response


