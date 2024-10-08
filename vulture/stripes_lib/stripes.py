import pandas as pd
import matplotlib.pyplot as plt
import xarray as xr
import numpy as np
import fsspec
from convertbng.util import convert_bng
from xhtml2pdf import pisa
from io import BytesIO
import os


print("""NOTE: I had to hack the walrus operator in one line of fsspec, not supported in Py3.7:
  File "/usr/local/Miniconda3-py39_4.12.0-Linux-x86_64/envs/vulture/lib/python3.7/site-packages/fsspec/implementations/reference.py", line 797
    if x := self.dataframes[pref]["raw"][i]:
""")

"""
NOTE: I also had to hack the following objects in this library:
/usr/local/Miniconda3-py39_4.12.0-Linux-x86_64/envs/vulture/lib/python3.7/site-packages/pywps/inout/formats/__init__.py

FORMATS
_FORMATS

- added "PDF" and "PNG" to these.
"""

# Define the cache as a dictionary
CACHE = {}

# Define some global constants for the colour maps
DEFAULT_CMAP = "RdBu_r"
N_COLOURS = 20


def get_colour_map(cmap_name=DEFAULT_CMAP, n_colours=-1):
    """
    Return a colour map object based on colour map name and the number of colour bins.
    Set n_colours to -1 to get a continuous colour map.
    """
    args = [cmap_name]
    if n_colours > 1: 
        args.append(n_colours)

    cmap = plt.get_cmap(*args)
    cmap._init()
    return cmap


def rgba_to_hex(r, g, b, a=None):
    """
    Convert (red, green, blue, alpha) tuples and convert to a Hex string to represent the colour.
    """
    r, g, b = [int(i * 255) for i in (r, g, b)]
    return "#" + "".join([("0" + hex(i).split("x")[1])[-2:] for i in (r, g, b)])


def get_colours_lookup(cmap_name=DEFAULT_CMAP, n_colours=N_COLOURS): 
    """
    Based on a colour map and a number of requested colours, return a lookup dictionary of:
        - (red, green, blue): colour name
    """
    cmap = get_colour_map(cmap_name, n_colours)
    assert cmap.N == n_colours

    cols = [((r, g, b), f"colour_{(i + 1):02d}") for i, (r, g, b, a) in sorted(enumerate(cmap._lut))]
    print("NOTE: The last three rows are the colours for data low and high out-of-range values and for masked values.")
    return dict(cols)


# Now let's define a class to create a stripes dataset and plot.
# First define some global constants
KERCHUNK_PATH = "/usr/local/src/vulture/vulture/stripes_lib/haduk-grid1.json"
SPATIAL_PROXIMITY_THRESHOLD = 0.05
DEFAULT_REFERENCE_PERIOD = (1901, 2000)


class HadUKStripesMaker:
    """
    A class to create climate stripes for different locations.
    You can tweak:
       - the location
       - the time range
       - the time range of the reference period (used for the average value)
       - the colour map used
       - the number of colours used
       - the spatial threshold used for checking a grid box centre is near the requested location

    Use as follows:
    >>> stripes_maker = HadUKStripesMaker()
    >>> df = stripes_maker.create(51.23, -1.23, )
    >>> stripes_maker.show_plot()
    >>> strips_maker.show_table()

    To specify a time range and a different number of colours and a blue-green colour map:
    >>> stripes_maker.create(51.23, -1.23, n_colours=10, cmap_name="winter", time_range=(1950, 2010), 
               output_file="new-stripes.png")
    """

    def __init__(self, kerchunk_path=KERCHUNK_PATH, 
                spatial_threshold=SPATIAL_PROXIMITY_THRESHOLD,
                reference_period=DEFAULT_REFERENCE_PERIOD,
                cmap_name=DEFAULT_CMAP,
                n_colours=N_COLOURS):

        self.kerchunk_path = kerchunk_path
        self.spatial_threshold = spatial_threshold
        self.reference_period = reference_period
        self.cmap_name = cmap_name
        self.n_colours = n_colours

        self.latest_df = None
        self.latest_plot = None
        self.latest_request = None

    def _check_location_is_near(self, lat, lon, point_ds, ds):
        """
        Checks that selected eastings and northings (in BNG coordinates) are within the lat/lon threshold of
        the `lat` and `lon` requested by the user.
    
        Raises an exception if outside the acceptable threshold.
    
        Returns tuple of: (eastings, northings)
        """
        y = float(point_ds.projection_y_coordinate.values)
        x = float(point_ds.projection_x_coordinate.values)
        
        lat_diff = abs(float(ds.latitude.sel(projection_y_coordinate=y, projection_x_coordinate=x)) - lat)
        lon_diff = abs(float(ds.longitude.sel(projection_y_coordinate=y, projection_x_coordinate=x)) - lon)
    
        assert lat_diff < self.spatial_threshold, f"Lat diff is too big: {lat_diff}"
        assert lon_diff < self.spatial_threshold, f"Lon diff is too big: {lon_diff}"
    
        return (x, y)
        
    def _extract_time_series_at_location(self, lat, lon, years=None, ref_period=DEFAULT_REFERENCE_PERIOD):
        """
        Read the data from the data files.
        Return a dictionary containing keys:
            - temp_series: the extracted temperature series
            - demeaned_temp_series: the temperature series with the mean of the reference period subtracted
            - eastings: actual easting of grid box centre (British National Grid)
            - northings: actual northing of grid box centre (British National Grid)
            - lat: actual latitude of grid box centre
            - lon: actual longitude of grid box centre
        """
        # Create a mapper to load the data from Kerchunk
        compression = "zstd" if self.kerchunk_path.split(".")[-1].startswith("zst") else None
        mapper = fsspec.get_mapper("reference://", fo=self.kerchunk_path, target_options={"compression": compression})

        # Create an Xarray dataset that will read from the NetCDF data files
        print("opening kerchunk...need bigger arrays and specify duplicate coords and lat lon from each")
        ds = xr.open_zarr(mapper, consolidated=False, use_cftime=True, decode_timedelta=False)
    
        print("convert to northings, eastings...")
        requested_eastings, requested_northings = [i[0] for i in convert_bng(lon, lat)] 
     
        print("extract nearest grid point (with time subset if specified)...")
        start_year, end_year = (str(years[0]), str(years[1])) if years \
                                else (str(ds.time.min().dt.year.values), str(ds.time.max().dt.year.values))
        temp_series = ds.tas.sel(projection_y_coordinate=requested_northings, 
                                 projection_x_coordinate=requested_eastings,
                                 method="nearest").sel(time=slice(start_year, end_year))
    
        # Check the chosen location is near the requested location
        print("check data point is close enough to the requested location (within spatial threshold)...")
        actual_eastings, actual_northings = self._check_location_is_near(lat, lon, temp_series, ds)
    
        # Get mean over reference period
        print("calculate the mean over the reference period...")
        reference_mean = temp_series.sel(time=slice(str(ref_period[0]), str(ref_period[1]))).mean()
    
        # Construct content to return
        response = {
            "temp_series": temp_series.squeeze().compute(),
            "demeaned_temp_series": (temp_series - reference_mean).squeeze().compute(),
            "eastings": actual_eastings, "northings": actual_northings,
            "lat": float(ds.latitude.sel(projection_y_coordinate=actual_northings, projection_x_coordinate=actual_eastings)),
            "lon": float(ds.longitude.sel(projection_y_coordinate=actual_northings, projection_x_coordinate=actual_eastings))
        }
        print("Returning data objects...")
        return response

    def create(self, lat, lon, n_colours=N_COLOURS, cmap_name=DEFAULT_CMAP, time_range=None, 
               output_file="climate-stripes.png", range_buffer=0.2):
        """
        Creates both a plot and a dataset (as a `pandas DataFrame`) based on input requirements.
        
        NOTE: range_buffer can be modified to ensure that the colours are all within range of the cmap.
        Returns a `pandas.DataFrame` object.
        """
        self.cmap_name = cmap_name or self.cmap_name
        time_range = tuple(time_range) if time_range else time_range

        n_colours = n_colours if n_colours > 0 else self.n_colours
        args = (lat, lon, n_colours, cmap_name, range_buffer, time_range)

        # Use the cache if the request has already been made
        if args in CACHE.keys():
            print("Loading from cache...")
            data = CACHE[args]
        else:
            print("Loading from file...")
            resp = self._extract_time_series_at_location(lat, lon, time_range)
            years = resp["temp_series"].time.dt.year
        
            actual_values = resp["temp_series"].values
            stripes_data = resp["demeaned_temp_series"].values
            data = {"years": years, "actual_values": actual_values, "stripes_data": stripes_data}
            print("Saving to cache...")
            CACHE[args] = data

        self.latest_request = {
            "lat": lat, "lon": lon, "n_colours": n_colours,
            "cmap_name": cmap_name, "time_range": (time_range or (int(data["years"].min()), int(data["years"].max())))
        }
        
        print("Downloaded data...")
        # Unpack dictionary
        years, actual_values, stripes_data = data["years"], data["actual_values"], data["stripes_data"]
    
        print("Min and max:", stripes_data.min(), stripes_data.max())
    
        # Add a buffer around the lower and upper boundaries - to use only values within the colourmap
        normalised_data = plt.Normalize(stripes_data.min() - range_buffer, stripes_data.max() + range_buffer)
        cmap = get_colour_map(self.cmap_name, n_colours)
        
        fig, ax = plt.subplots(figsize=(10, 2))
        
        print("Starting plot")
    
        colours = []
        
        for i in range(stripes_data.shape[0]):
            actual_value = actual_values[i]
            year = years[i]
            normalised_value = normalised_data(stripes_data[i])
            rgba_colour = cmap(normalised_value)
            colours.append(rgba_colour)
    
            # collected.append([actual_value, normalised_value, colour])
            ax.axvspan(
                xmin=i - 0.5, xmax=i + 0.5, color=rgba_colour
            )
        
        ax.axis("off")
        plt.savefig(output_file)
        print(f"Saved image file: {output_file}")
        self.latest_plot = output_file

        df = pd.DataFrame({
            "years": years,
            "temp_value": actual_values,
            "temp_demeaned": stripes_data,
            "hex_colour": [rgba_to_hex(r, g, b) for (r, g, b, a) in colours],
            "red": [col[0] for col in colours],
            "green": [col[1] for col in colours],
            "blue": [col[2] for col in colours]
        })

        self.latest_df = self._extend_dataframe(df, cmap_name, n_colours)
        return self.latest_df

    def _extend_dataframe(self, df, cmap_name, n_colours):
        """
        Extends and returns the DataFrame with "colour_block" and "colour" columns.
        "colour_block" is empty - ready for highlighted rendering with `.show_table()`.
        """
        col_lookup = get_colours_lookup(cmap_name, n_colours)
        df["colour_block"] = ""
        df.loc[:, "colour"] = df.apply(lambda row: col_lookup[(row["red"], row["green"], row["blue"])], axis=1)
        return df

    def _get_colour_mapping(self, df):
        tmp_df = df[["colour", "hex_colour"]].drop_duplicates().sort_values("colour")
        dct = pd.Series(tmp_df.hex_colour.values, index=tmp_df.colour).to_dict()
        return {key: f"background-color: {colour}" for key, colour in dct.items()}

    def show_table(self, full=True):
        """
        Show the latest data table created.
        """
        print(f"Request details: {self.latest_request}")

        if full:
            df2 = self.latest_df.copy()
            df2["colour_block"] = ""
        else:
            df2 = pd.DataFrame(self.latest_df[["colour"]].value_counts().sort_values().sort_index())
            df2["colour_block"] = ""
            df2 = df2.reset_index()
        
        def _highlight_cols(df, full_df=self.latest_df):
            style_df = df.copy().astype(str)
            style_df.loc[:,:] = 'background-color: none'
            colour_dict = self._get_colour_mapping(full_df)
            style_df["colour_block"] = df.colour.map(colour_dict)
            return style_df
        
        return df2.style.apply(highlight_cols, axis=None)

    def show_plot(self):
        "Show the latest plot."
        print(f"Image location: {self.latest_plot}")
        return Image(self.latest_plot)
    
    def clear_cache(self):
        "Empties global cache dictionary."
        keys = list(CACHE.keys())

        for key in keys:
            del CACHE[key]


HTML_TEMPLATE = """<html>
<head>

<style>
    body {{font-family: "Times New Roman", Times, serif; font-size: 12px;}}
    table, tr, th, td {{border: 1px solid black; padding: 2px;}}
    td {{min-width: 100px; text-align: right;}}
</style>

</head>
<body>
    <h1>Climate Stripes for:</h1>
    {project}
    <p>Latitude: {lat}&deg;,  Longitude: {lon}&deg;.</p>
    <p>Time period: {time_range}</p>
    <p>Using: {n_colours} colours</p>
    </br/>
    <img src="{png_file}" />
    <br/>
     
    <h1>Table 1: Temperature variations from the average, and colours per year.</h1>

{table_1}

    <h1>Table 2: Colour table</h1>

{table_2}

<h1>Citation</h1>

<p>Met Office; Hollis, D.; McCarthy, M.; Kendon, M.; Legg, T. (2023): HadUK-Grid Gridded Climate Observations on a 60km grid over the UK, v1.2.0.ceda (1836-2022). NERC EDS Centre for Environmental Data Analysis, 30 August 2023. doi:10.5285/22df6602b5064b1686dda7e9455f86fc. <a href="https://dx.doi.org/10.5285/22df6602b5064b1686dda7e9455f86fc">https://dx.doi.org/10.5285/22df6602b5064b1686dda7e9455f86fc</a>.</p>

<h1>Additional information</h1>
<p>If you like this please share with friends and family! You can point them towards our page 
https://www.ceda.ac.uk/outreach where there's some more resources, links to further information 
and a place for you to share anything cool you do with this!</p>

</body>
</html>"""


# Create an extension to write to HTML and PDF outputs

class HadUKStripesRenderer(HadUKStripesMaker):
    
    def _get_table(self, table):
        ldf = self.latest_df
        colour_dict = self._get_colour_mapping(ldf)

        if table == 1:
            df = ldf.copy()
            row_vars = "years temp_value temp_demeaned hex_colour red green blue colour".split()
        elif table == 2:
            df = pd.DataFrame(ldf["colour"].value_counts().sort_values().sort_index())
            df = df.rename(columns={"colour": "colour_count"})
            df["colour"] = df.index

            df["colour_block"] = ""
            df = df.reset_index()
            row_vars = ["colour", "colour_count"]

        df["colour_block"] = df["colour"].map(colour_dict)

        normal_rows = "\n".join([f"        <td>{{{row_var}}}</td>\n" for row_var in row_vars])

        row_template = f"""
    <tr>
{normal_rows}
      <td style="{{colour_block}}">         </td>
    </tr>"""

        table_rows = ""

        for idx, row in df.round(5).iterrows():
            html_row = row_template.format(**row)
            table_rows += html_row

        col_names = row_vars + ["actual_colour"]
        head_rows = "\n".join([f"      <th>{col_name}</th>" for col_name in col_names])

        html_table = f"""<table>
  <thead>
{head_rows}
  </thead>
  <tbody>
    {table_rows}
  </tbody>
</table>
"""
        return html_table
    
    def to_html(self, html_file=None, project_name=None):
        """
        Return HTML content as a string (or write to `html_file` if defined).
        """
        if project_name:
            project = f"<p><b>{project_name}</b></p>"
        else:
            project = ""

        content = self.latest_request.copy()
        content["project"] = project
        content["png_file"] = self.latest_plot
        content["png_url"] = os.path.basename(self.latest_plot)

        content["table_1"] = self._get_table(table=1)
        content["table_2"] = self._get_table(table=2)
        
        html = HTML_TEMPLATE.format(**content)

        if html_file:
            with open(html_file, "w", encoding="utf-8") as file:
                file.write(html)

        return html

    def to_pdf(self, pdf_file, project_name=None):
        html_content = self.to_html(project_name=project_name)
        
        # Create a BytesIO object to store the PDF output
        pdf_output = BytesIO()
        
        # Convert the HTML content to a PDF document
        pisa.CreatePDF(html_content, dest=pdf_output, encoding='utf-8')
        
        # Open a PDF file for writing in binary mode
        with open(pdf_file, "wb") as pdf_writer:
            pdf_writer.write(pdf_output.getvalue())

        return pdf_file





#def test_HadUKStripesMaker():
#    stripes_maker = HadUKStripesRenderer()

    # RAL_LAT, RAL_LON = 51.570664384, -1.308832098

#    df = stripes_maker.create(51.570664384, -1.308832098, output_file="/tmp/new-stripes2.png")
#    html = stripes_maker.to_html(html_file="/tmp/output.html", project_name="My great project")
#    pdf_file = stripes_maker.to_pdf("/tmp/output.pdf", project_name="Another project")
    #df = stripes_maker.create(51.23, -1.23, n_colours=10, cmap_name="winter", time_range=(1950, 2010), output_file="new-stripes.png")

    #stripes_maker.show_table()
    #stripes_maker.show_table(full=False)
    #stripes_maker.show_plot()


