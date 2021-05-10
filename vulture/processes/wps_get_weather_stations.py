import os

from pywps import Process, LiteralInput, ComplexOutput, BoundingBoxInput
from pywps import FORMATS

from pywps.app.Common import Metadata

from midas_extract.vocabs import DATA_TYPES, UK_COUNTIES
from goldfinch.util import (get_station_list, validate_inputs, 
    WEATHER_STATIONS_FILE_NAME, DEFAULT_DATE_RANGE)

import logging
LOGGER = logging.getLogger("PYWPS")


class GetWeatherStations(Process):
    """A process getting UK weather stations."""
    def __init__(self):
        inputs = [
            # LiteralInput('start', 'Start Date Time',
            #              abstract='The first date/time for which to search for operating weather stations.',
            #              data_type='dateTime',
            #              default='2017-10-01T12:00:00Z'),
            # LiteralInput('end', 'End Date Time',
            #              abstract='The last date/time for which to search for operating weather stations.',
            #              data_type='dateTime',
            #              default='2018-02-25T12:00:00Z'),
            LiteralInput('DateRange', 'Date Range',
                          abstract='The date range to search for operating weather stations.',
                          data_type='string',
                          default=DEFAULT_DATE_RANGE,
                          min_occurs=0,
                          max_occurs=1),
            BoundingBoxInput('bbox', 'Bounding Box',
                             abstract='The spatial bounding box within which to search for weather stations.'
                                      ' This input will be ignored if counties are provided.',
                             crss=['-12.0, 49.0, 3.0, 61.0,epsg:4326'],
                             min_occurs=0,
                             max_occurs=1),
            # LiteralInput('bbox', 'Bounding Box',
            #              abstract='The spatial bounding box within which to search for weather stations.'
            #              ' This input will be ignored if counties are provided.'
            #              ' Provide the bounding box as: "W,S,E,N".',
            #              data_type='string',
            #              min_occurs=0,
            #              max_occurs=1),
            LiteralInput('counties', 'Counties',
                         abstract='A list of counties within which to search for weather stations.',
                         data_type='string',
                         allowed_values=UK_COUNTIES,
                         min_occurs=0,
                         max_occurs=len(UK_COUNTIES)),
            LiteralInput('datatypes', 'Data Types',
                         data_type='string',
                         allowed_values=DATA_TYPES,
                         min_occurs=0,
                         max_occurs=len(DATA_TYPES))
        ]
        outputs = [
            ComplexOutput('output', 'Output',
                          abstract='Station list.',
                          as_reference=True,
                          supported_formats=[FORMATS.TEXT])]

        super(GetWeatherStations, self).__init__(
            self._handler,
            identifier='GetWeatherStations',
            title='Get Weather Stations',
            abstract='The "GetWeatherStations" process allows the user to identify'
                     ' a set of Weather Station numeric IDs.'
                     ' These can be selected using temporal and spatial filters'
                     ' to derive a list of stations'
                     ' that the user is interested in. The output is a text file '
                     ' containing one station ID per line.'
                     ' Please see the disclaimer.',
            keywords=['stations', 'uk', 'demo', 'weather', 'observations'],
            metadata=[
                Metadata('CEDA WPS UI', 'https://ceda-wps-ui.ceda.ac.uk'),
                Metadata('Goldfinch WPS User Guide', 'https://goldfinch.readthedocs.io'),
                Metadata('Disclaimer', 'https://help.ceda.ac.uk/article/4642-disclaimer')
            ],
            version='2.0.0',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):
        # Now set status to started
        response.update_status('Job is now running', 0)

        inputs = validate_inputs(request.inputs, 
            defaults={'DateRange': DEFAULT_DATE_RANGE})

        # Add output file
        stations_file = os.path.join(self.workdir, WEATHER_STATIONS_FILE_NAME)

        get_station_list(
            counties=inputs['counties'],
            bbox=inputs['bbox'],
            start=inputs['start'],
            end=inputs['end'],
            output_file=stations_file,
            data_type=inputs['datatypes']
        )

        # We can log information at any time to the main log file
        LOGGER.info(f'Written output file: {stations_file}')

        response.outputs['output'].file = stations_file
        return response
