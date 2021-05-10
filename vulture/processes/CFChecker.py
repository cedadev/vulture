"""
CFChecker.py
==================

Process module that holds the CFChecker class.

"""

# Standard library imports
import os, stat, time, sys, logging, commands

# WPS imports
from cows_wps.process_handler.fileset import FileSet, FLAG
import cows_wps.process_handler.process_support as process_support
from cows_wps.process_handler.context.process_status import STATUS
import processes.internal.ProcessBase.ProcessBase
from cows_wps.utils.common import downloadFromURL

import cdms2 as cdms
from cfchecker import cfchecks

# Import process-specific modules

# NOTE ABOUT LOGGING:
# You can log with the context.log object

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class CFChecker(processes.internal.ProcessBase.ProcessBase.ProcessBase):

    # Define arguments that we need to set from inputs
    # Based on args listed in process config file
    # This must be defined as 'args_to_set = []' if no arguments!
    args_to_set = ["CheckAgainstCFVersion", "NCFilePath", "NCFileURL", "NCFileUpload"]

    # Define defaults for arguments that might not be set
    # A dictionary of arguments that we can over-write default values for
    # Some args might be mutually-exclusive or inclusive so useful to set 
    # here as well as in the config file.
    input_arg_defaults = {"CheckAgainstCFVersion": "auto", "NCFilePath": None, 
                          "NCFileURL": None, "NCFileUpload": None}

    # Define a dictionary for arguments that need to be processed 
    # before they are set (with values as the function doing the processing).
    arg_processers = {}

    def _extractConventionsAttribute(self, fpath):
        """
        Returns value of "Conventions" global attribute from NetCDF
        file at ``fpath`` or returns None if not found.
        """
        f = cdms.open(fpath)
        conv = getattr(f, "Conventions", None)
        f.close()
        return conv
    
    def _executeProc(self, context, dry_run):
        """
        This is called to step through the various parts of the process 
        executing the actual process if ``dry_run`` is False and just 
        returning information on the volume and duration of the outputs
        if ``dry_run`` is True.
        """
        # Call standard _setup
        self._setup(context)
        a = self.args

        if not dry_run:
            # Now set status to started
            context.setStatus(STATUS.STARTED, 'Job is now running', 0)

        # Add output file 
        outputFile = 'cfchecker_output.txt'
        outputFilePath = os.path.join(context.outputDir, outputFile)

        if not dry_run:
            # Get the latest CF version
            conv_to_use = a.get("CheckAgainstCFVersion", "auto")

            if conv_to_use == "auto":
                conv = self._extractConventionsAttribute(self.nc_file_path)
                if conv:
                    version = cfchecks.CFVersion(conv)
                else:
                    version = cfchecks.newest_version
            else:
                version = cfchecks.CFVersion(conv_to_use)

            # Redirect standard output so we can capture it
            class Stdout(object):
                def __init__(self):
                    self.data = ""
                def write(self, data):
                    self.data += data

            tmp_stdout = sys.stdout
            sys.stdout = Stdout()

            checker = cfchecks.CFChecker(cfStandardNamesXML = cfchecks.STANDARDNAME, 
                                         cfAreaTypesXML = cfchecks.AREATYPES,
                                         version = version)

            rc = checker.checker(self.nc_file_path)
            resp = sys.stdout.data
            sys.stdout = tmp_stdout

            fout = open(outputFilePath, "w")
            fout.write(resp)
            fout.close()

            size = os.path.getsize(outputFilePath)
        
            # Add the output list to the XML output section: ProcessSpecificContent
            context.outputs['ProcessSpecificContent'] = {"CFCheckerOutput": resp} 

        else:
            # Make it up for dry run
            size = 2345 

        if not dry_run:
            # We can log information at any time to the main log file
            context.log.info('Written output file: %s' % outputFilePath)
        else:
            context.log.debug("Running dry run.")



    def _validateInputs(self):
        """
        Runs specific checking of arguments and their compatibility.
        Sets ``self.nc_file_path`` for use later.
        """
        nc_url = self.args.get("NCFileURL", "")

        if nc_url:
            data = downloadFromURL(nc_url)
            fname = os.path.split(nc_url)[1]
            if not fname:
                fname = "testfile.nc"

            self.tmp_dir = os.path.join(self.context.processDir, 'tmp')
            self.nc_file_path = os.path.join(self.tmp_dir, fname)
            f = open(self.nc_file_path, "wb")
            f.write(data)
            f.close()
        
        elif self.args.get("NCFilePath", ""):
            self.nc_file_path = self.args["NCFilePath"]

        elif self.args.get("NCFileUpload", ""):
            self.nc_file_path = self.args["NCFileUpload"]

        else:
            raise Exception("Invalid arguments provided. Must provide location of NetCDF file as input.")
