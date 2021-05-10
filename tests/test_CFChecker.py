"""
test_process_template.py
========================

Tests for the "CFChecker" process.

To run, just do:

 python processes/local/test_process_template.py

Define the tests below and add as many as you want.

"""

from cows_wps.tests.process_tester import *


# Process identifier
identifier = "CFChecker"

# Define as many sets of inputs and outputs as you need 
# They are all referenced in the tester.addTest(...) calls below so it 
# fine to re-use them where appropriate
#
# NOTE: All inputs should be represented as strings in the inputs dictionaries
#
inputs_1 = {'CheckAgainstCFVersion': 'auto', 'NCFilePath': '/disks/kona2/old-kona1/wps_test/cache/example_data.nc'}
outputs_1 = { }

inputs_2 = { }
outputs_2 = { }

# Define configuration information as required in the ``options`` dictionary
# Supported parameters are:
#   verbose: Boolean	- increases the amount of information shown if True
#
options = {"verbose": True, "similarity_threshold": 0.3}

#-------------------------------------------------------------------
# Now we create the test and run the tests
# Define the tester which actually runs the tests
tester = ProcessTester(identifier)

# Add as many tests as you like here, each called as follows
tester.addTest(inputs_1, outputs_1, options)
#tester.addTest(inputs_2, outputs_2, options)

# And now run all the tests
tester.runAllTests()
