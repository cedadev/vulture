from .wps_cf_check import CFCheck
from .wps_plot_climate_stripes import PlotClimateStripes

processes = [
    CFCheck(),
    PlotClimateStripes()
]
