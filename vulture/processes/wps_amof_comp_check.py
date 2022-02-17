import requests
import os
import sys
import subprocess as sp

from pywps import LiteralInput, Process, FORMATS, Format, ComplexOutput
from pywps.app.Common import Metadata
from pywps.app.exceptions import ProcessError
from pywps import configuration

from ..utils import get_input

import logging
LOGGER = logging.getLogger("PYWPS")


class AMOFCompCheck(Process):
    supported_checks_versions = ["2.0"]

    def __init__(self):
        inputs = [
            LiteralInput(
                "AMOFChecksVersion",
                "AMOF Checks Version",
                abstract=("Version of the AMOF Compliance Checks that the file should be checked against. "
                          "E.g.: auto, 2.0."),
                allowed_values=["auto"] + self.supported_checks_versions,
                data_type="string",
                default="auto",
                min_occurs=1,
                max_occurs=1
            ),
            LiteralInput(
                "FileURL",
                "File URL",
                abstract="URL to a file accessible via the internet.",
                data_type="string",
                min_occurs=0,
                max_occurs=1
            ),
            LiteralInput(
                "FileUpload",
                "File Upload",
                abstract="You may upload a file to this service using this loader.",
                data_type="string",
                min_occurs=0,
                max_occurs=1
            ),
            LiteralInput(
                "FilePath",
                "File Path",
                abstract="A file path pointing to a file in the CEDA Archive.",
                data_type="string",
                min_occurs=0,
                max_occurs=1
            ),
        ]

        outputs = [
            ComplexOutput('output', 'Output',
                          abstract='Outputs from the AMOF Compliance Checker',
                          as_reference=True,
                          supported_formats=[FORMATS.TEXT])]

        super(AMOFCompCheck, self).__init__(
            self._handler,
            identifier="AMOFCompCheck",
            title="AMOF Compliance Checker",
            abstract="Run the AMOF Compliance Checker on a data file.",
            keywords=['check', 'amof', 'ncas', 'observation', 'checking', 'standards',
                      'ocean', 'atmosphere', 'instrument'],
            metadata=[
                Metadata('CEDA WPS UI', 'https://ceda-wps-ui.ceda.ac.uk'),
                Metadata('CEDA WPS', 'https://ceda-wps.ceda.ac.uk'),
                Metadata('AMOF Compliance Checker', 'https://some.where.or.other'),
                Metadata('Disclaimer', 'https://help.ceda.ac.uk/article/4642-disclaimer')
            ],
            version='1.0.0',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

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

    def _get_file_path(self, inputs):
        """
        Parse the inputs to decide which file to check, return the local path to it.
        """
        # If URL provided, then use that
        url = get_input(inputs, "FileURL")
        file_upload = get_input(inputs, "FileUpload")
        file_path = get_input(inputs, "FilePath")

        if url:
            # Use downloaded file
            file_path = self._download_file(url)

        elif file_upload:
            file_path = self._map_url_to_path(file_upload)

        elif file_path:
            file_path = file_path

        else:
            raise Exception()

        LOGGER.info(f"Data file to check: {file_path}")
        return file_path

    def _wrap_checker(self, checks_version, input_path):
        output_dir = self.workdir

        #input_path = "/gws/smf/j04/cedaproc/amf-example-files/ncas-anemometer-1_ral_29001225_mean-winds_v0.1.nc"
        CHECKS_VERSION = "v2.0"
        PYESSV_ARCHIVE_HOME = "/gws/smf/j04/cedaproc/amof-checker/AMF_CVs-2.0.0/pyessv-vocabs"
        CHECKS_DIR = "/gws/smf/j04/cedaproc/amof-checker/amf-compliance-checks-2.0.0/checks"

        cmd = "source /gws/smf/j04/cedaproc/amof-checker/setup-checks-env.sh; "
        cmd += f"amf-checker --yaml-dir {CHECKS_DIR} --version {CHECKS_VERSION} -f text -o {output_dir} {input_path}"

        sp.run(f'bash -c "{cmd}"', shell=True, env={"PYESSV_ARCHIVE_HOME": PYESSV_ARCHIVE_HOME, "CHECKS_DIR": CHECKS_DIR})
        output_path = os.path.join(output_dir, os.path.basename(input_path) + ".cc-output")

        new_path = os.path.join(output_dir, "check-output.txt")
        os.rename(output_path, new_path)
        return new_path 

    def _handler(self, request, response):
        """
        Runs the AMOF Compliance Checker on a file.
        """
        response.update_status('Job is now running', 0)

        # Determine the  file to check
        try:
            file_path = self._get_file_path(request.inputs)
        except Exception:
            raise ProcessError(("User must provide one input from: FileURL, "
                                "FileUpload or FilePath."))

        # Get the checks version to use
        checks_version = "v" + get_input(request.inputs, "AMOFChecksVersion").replace("auto", self.supported_checks_versions[0])

        # Set output file
        output_file = os.path.join(self.workdir, 'amof_checker_output.txt')

        # Redirect standard output so we can capture it
#        class Stdout(object):
#            def __init__(self):
#                self.data = ""
#            def write(self, data):
#                self.data += data

#        tmp_stdout = sys.stdout
#        sys.stdout = Stdout()

        try:
            output_file = self._wrap_checker(checks_version, file_path)
        except Exception:
            raise ProcessError('Could not run AMOF Compliance Checker on input file') 

#        output = sys.stdout.data

        # Put standard output back in the right place
#        sys.stdout = tmp_stdout

        # Write the results to the output file
#        with open(output_file, "w") as fout:
#            fout.write(output)

        response.update_status('AMOF-Comp-Checks completed', 90)

        LOGGER.info(f'Written output file: {output_file}')

        response.outputs['output'].file = output_file

        return response

