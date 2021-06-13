import requests
import os
import sys
import re

from netCDF4 import Dataset

from cfchecker import cfchecks

from pywps import LiteralInput, Process, FORMATS, Format, ComplexOutput
from pywps.app.Common import Metadata
from pywps.app.exceptions import ProcessError
from pywps import configuration

import logging
LOGGER = logging.getLogger("PYWPS")


class CFCheck(Process):
    def __init__(self):
        inputs = [
            LiteralInput(
                "CFVersion",
                "CF Version",
                abstract=("Version of the CF Conventions that the NetCDF file should be checked against. "
                          "E.g.: auto, 1.6, 1.7, 1.8."),
                allowed_values=["auto", "1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8"],
                data_type="string",
                default="auto",
                min_occurs=1,
                max_occurs=1
            ),
            LiteralInput(
                "NCFileURL",
                "NC File URL",
                abstract="URL to a NetCDF file accessible via the internet.",
                data_type="string",
                min_occurs=0,
                max_occurs=1
            ),
            LiteralInput(
                "NCFileUpload",
                "NC File Upload",
                abstract="You may upload a NetCDF file to this service using this loader.",
                data_type="string",
                min_occurs=0,
                max_occurs=1
            ),
            LiteralInput(
                "NCFilePath",
                "NC File Path",
                abstract="A file path pointing to a NetCDF file on the server.",
                data_type="string",
                min_occurs=0,
                max_occurs=1
            ),
        ]

        outputs = [
            ComplexOutput('output', 'Output',
                          abstract='Outputs from the CF-Checker',
                          as_reference=True,
                          supported_formats=[FORMATS.TEXT])]

        super(CFCheck, self).__init__(
            self._handler,
            identifier="CFCheck",
            title="CF-Checker",
            abstract="Run the CF-Checker on a NetCDF file.",
            keywords=['check', 'cf', 'conventions', 'climate', 'forecasts', 'checking', 'standards',
                      'ocean', 'atmosphere'],
            metadata=[
                Metadata('CEDA WPS UI', 'https://ceda-wps-ui.ceda.ac.uk'),
                Metadata('CEDA WPS', 'https://ceda-wps.ceda.ac.uk'),
                Metadata('CF-Checker source', 'https://github.com/cedadev/cf-checker'),
                Metadata('CF Conventions', 'https://cfconventions.org/'),
                Metadata('Disclaimer', 'https://help.ceda.ac.uk/article/4642-disclaimer')
            ],
            version='1.0.0',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _get_input(self, inputs, key, default=None):
        if key in inputs:
            return inputs[key][0].data

        return default

    def _download_file(self, url):
        response = requests.get(url)
        downloaded_file = response.content

        fpath = os.path.join(self.workdir, 'testfile.nc')

        if response.status_code == 200:
            with open(fpath, 'wb') as f:
                f.write(response.content)
        else:
            raise ProcessError('Unable to download data file provided as input.')

        return fpath

    def _map_url_to_path(self, url):
        """
        Takes a URL (from the UI/client server) and maps the path to the local
        file system. Returns that path.
        """
        # If the client sent a local file path, just use that
        if os.path.isfile(url):
            return url

        # If a URL was sent, then map that to a cache dir
        cache_dir = configuration.get_config_value("server", "shared_cache_dir")
        if cache_dir not in url:
            raise ProcessError('Could not access uploaded file via shared cache.')

        return os.path.join(cache_dir, url.split(cache_dir)[-1].lstrip('/'))

    def _get_nc_path(self, inputs):
        """
        Parse the inputs to decide which file to check, return the local path to it.
        """
        # If URL provided, then use that
        nc_url = self._get_input(inputs, "NCFileURL")
        nc_file_upload = self._get_input(inputs, "NCFileUpload")
        nc_file_path = self._get_input(inputs, "NCFilePath")

        if nc_url:
            # Use downloaded file
            nc_path = self._download_file(nc_url)

        elif nc_file_upload:
            nc_path = self._map_url_to_path(nc_file_upload)

        elif nc_file_path:
            nc_path = nc_file_path

        else:
            raise ProcessError(("User must provide one input from: NCFileURL, "
                                "NCFileUpload or NCFilePath."))

        LOGGER.info(f"NetCDF file to cf-check: {nc_path}")
        return nc_path

    def _resolve_conventions_version(self, inputs, nc_path):
        """
        Use the user input and/or the file version to decide the Conventions
        version to test the file against.
        """
        convention_version = self._get_input(inputs, "CFVersion", "auto")
        AUTO = 'auto'

        if convention_version == AUTO:
            ds = Dataset(nc_path)
            conv = getattr(ds, 'Conventions', AUTO)
            ds.close()

            # Extract only the CF-relevant part of any compound conventions
            cf_conv = [c.strip() for c in re.split('[,;]', conv) if c.strip().startswith('CF')][0]

            if cf_conv:
                version = cfchecks.CFVersion(cf_conv)
            else:
                version = cfchecks.newest_version
        else:
            version = cfchecks.CFVersion(convention_version)

        return version

    def _handler(self, request, response):
        """
        Runs the CF-Checker on a NetCDF file.
        """
        response.update_status('Job is now running', 0)

        # Determine the NetCDF file to check
        nc_path = self._get_nc_path(request.inputs)

        # Get the CF version to use
        try:
            conventions_version = self._resolve_conventions_version(request.inputs, nc_path)
        except Exception:
            raise ProcessError('Cannot read NetCDF file')

        # Set output file
        output_file = os.path.join(self.workdir, 'cfchecker_output.txt')

        # Redirect standard output so we can capture it
        class Stdout(object):
            def __init__(self):
                self.data = ""
            def write(self, data):
                self.data += data

        tmp_stdout = sys.stdout
        sys.stdout = Stdout()

        try:
            checker = cfchecks.CFChecker(cfStandardNamesXML=cfchecks.STANDARDNAME,
                                         cfAreaTypesXML=cfchecks.AREATYPES,
                                         version=conventions_version)
        except Exception:
            raise ProcessError('Could not run CF-Checker on input file') 

        rc = checker.checker(nc_path)
        output = sys.stdout.data

        # Put standard output back in the right place
        sys.stdout = tmp_stdout

        # Write the results to the output file
        with open(output_file, "w") as fout:
            fout.write(output)

        response.update_status('CF-Checks completed', 90)

        LOGGER.info(f'Written output file: {output_file}')

        response.outputs['output'].file = output_file

        return response
