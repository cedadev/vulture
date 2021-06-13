import re

from netCDF4 import Dataset

from cfchecker import cfchecks


def get_input(inputs, key, default=None):
    """
    Find the input in inputs dictionary, using key as lookup.
    """
    if key in inputs:
        return inputs[key][0].data

    return default


def resolve_conventions_version(inputs, nc_path):
    """
    Use the user input and/or the file version to decide the Conventions
    version to test the file against.
    """
    convention_version = get_input(inputs, "CFVersion", "auto")
    AUTO = 'auto'

    # Read the file to get the conventions if "auto" is selected
    # If cannot find a valid conventions attribute, then use latest
    try:
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

        # If not "auto", check a valid string was provided,
        else:
            version = cfchecks.CFVersion(convention_version)

    # If problems with parsing/ascertaining conventions, use newest
    except Exception:
        version = cfchecks.newest_version

    return version

