from .wps_cf_check import CFCheck
from .wps_amof_comp_check import AMOFCompCheck

processes = [
    CFCheck(),
    AMOFCompCheck(),
]
