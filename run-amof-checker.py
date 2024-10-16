import subprocess as sp

cmd = "source /gws/smf/j04/cedaproc/amof-checker/setup-checks-env.sh; "
TEST_FILE = "/gws/smf/j04/cedaproc/amf-example-files/ncas-anemometer-1_ral_29001225_mean-winds_v0.1.nc"
CHECKS_VERSION = "v2.0"
PYESSV_ARCHIVE_HOME = "/gws/smf/j04/cedaproc/amof-checker/AMF_CVs-2.0.0/pyessv-vocabs"
CHECKS_DIR = "/gws/smf/j04/cedaproc/amof-checker/amf-compliance-checks-2.0.0/checks"
cmd += f"amf-checker --yaml-dir {CHECKS_DIR} --version {CHECKS_VERSION} {TEST_FILE}"

sp.run(f'bash -c "{cmd}"', shell=True, env={"PYESSV_ARCHIVE_HOME": PYESSV_ARCHIVE_HOME, "CHECKS_DIR": CHECKS_DIR})

