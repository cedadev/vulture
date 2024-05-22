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

import logging
LOGGER = logging.getLogger("PYWPS")


class PNG_FORMAT:
    def __repr__(self):
        return "PNG"
    def validate(self):
        return True
    def same_as(self):
        return True
    def json(self):
        return {"format": "PNG"}


class PlotClimateStripes(Process):

    IDENTIFIER = "PlotClimateStripes"
    TITLE = "Plot Climate Stripes"
    ABSTRACT = "TBA"
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

    def _define_input(self, name, long_name, abstract, dtype="string", allowed_values=None):
        return LiteralInput(
            name,
            long_name,
            abstract=abstract,
            data_type=dtype,
            allowed_values=allowed_values,
            min_occurs=1,
            max_occurs=1,
        )

    def _define_inputs(self):
        inputs = [
            self._define_input("latitude", "Lat", "Lat", "float"),
            self._define_input("longitude", "Lon", "Lon", "float")
        ] 
        return inputs

    def _define_outputs(self):
        outputs = [
            ComplexOutput('output', 'Output',
                          abstract='Output file',
                          as_reference=True,
                          supported_formats=[FORMATS.CSV])]
        return outputs


    def _handler(self, request, response):

        lat = get_input(request.inputs, "latitude")
        lon = get_input(request.inputs, "longitude")
        inputs = {"latitude": lat, "longitude": lon}

        #    except Exception as exc:
        #        raise ProcessError(f"An error occurred when converting to CSV: {str(exc)}")
        output_file = os.path.join(self.workdir, "stripes.png")
# "latlon.txt")
#        with open(output_file, "w") as writer:
#            writer.write(f"You requested: {lat}, {lon}")
        shutil.copy("/tmp/climate-stripes.png", output_file)
                
        response.update_status('Plot completed', 90)

        LOGGER.info(f'Written output file: {output_file}')
        response.outputs['output'].file = output_file
        return response
