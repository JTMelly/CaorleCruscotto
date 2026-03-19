# CaorleCruscotto
### Make XBeach models with Python.

![cruscotto](/images/cruscotto.png)

This collection of scripts attempts to mimic some of [Delft Dashboard's](https://doi.org/10.2166/hydro.2020.092) *XBeach bathymetry* and *model maker* tools functionality. A use case might involve creating model bathymetry from a gridded elevation (depth) raster file, extending model bathymetry offshore past depth of closure (if needed), and creating non-erodible and [Manning coefficient](https://www.fsl.orst.edu/geowater/FX3/help/8_Hydraulic_Reference/Mannings_n_Tables.htm) grids matching the *bed.dep* depth grid dimensions. Inspired by [Alerovere's Coastal Hydrodynamics](https://github.com/Alerovere/CoastalHydrodynamics) repository and [OpenEarth's xbeach-toolbox](https://github.com/openearth/xbeach-toolbox).

Tools should work as *Jupyter Notebooks* or in *Colabs* with limited tinkering. Blocks of code are organized into interactive chunks because we debug in production. [Conda-forge](https://conda-forge.org/) seems like a good option for managing packages and some required modules include:

*  `geopandas`
*  `matplotlib` 
*  `numpy`
*  `pandas`
*  `rasterio`
*  `scipy`
*  `shapely`

REMEBER TO ALWAYS USE RASTERS IN WELL-DEFINED UTM COORDINATES OR RISK DISASTER! 

## Make grid and bathymetry
Bring your own bathymetry. `MakeGridAndBathy.py` takes a raster file containing elevation (depth) information and interpolates to a user-defined grid, outputting the *.grd* and *.dep* files that XBeach will look for to run. With [rasterio](https://github.com/rasterio/rasterio) and [scipy](https://github.com/scipy/scipy) under the hood, so far it has worked starting from .tif and .asc files.

To use the resultant files, update *params.txt* with:

*   `xfile        = x.grd`
*   `yfile        = y.grd`
*   `depfile      = bed.dep`

Also remember to set `nx = _` and `ny = _` in *params.txt* accordingly (`nx` is always cross-shore and `ny` is always alongshore).

![grid plot](/images/grid.png)

## Extend grid and bathymetry
Feed `ExtendGridAndBathy.py` some *.grd* and *.dep* files and get back new, extended *.grd* and *.dep* files that reach an offshore target depth by applying a user-defined slope. 

Again, to use the resultant files, update *params.txt* with:

*   `xfile        = x_extended.grd`
*   `yfile        = y_extended.grd`
*   `depfile      = bed_extended.dep`

and set `nx = _` and `ny = _` in *params.txt* accordingly (`nx` is always cross-shore and `ny` is always alongshore).

![extended bathymetry plot](/images/extendedbathy.png)

## Make non-erodible layer
Make a non-erodible layer file, based on an *XBeach* model's *.grd* and *.dep* files, using `MakeNonErodible.py`. Two cases are possible:
1.  A single erodible sediment thickness value is applied to the entire model domain.
2.  Erodible/non-erodible areas are defined by a user-provided .geojson file and erodible areas are assigned a sediment thickness value based on user input.

To use the *ne_layer.dep* file produced, update *params.txt* with:
*   `ne_layer     = ne_layer.dep`
*   `struct       = 1` 


A special case might be an erodible sediment thickness of 0 (no erodible sediments) covering the entire model domain, though the same result could likely be achieved by updating *params.txt* with:
*   `morphology   = 0`
*   `sedtrans     = 0`

![non-erodible layer plot](/images/nonerodible.png)

## Make Manning layer
`MakeManning.py` makes a *.dep* file containing [Manning coefficients](https://www.fsl.orst.edu/geowater/FX3/help/8_Hydraulic_Reference/Mannings_n_Tables.htm) for each model grid node, shaped after an *XBeach* model's *.grd* and *.dep* files. Users must supply a .geojson file comprised of area polygons and an attribute field titled "manning" containing the number values.

To use the output file, update *params.txt* with:
*   `bedfriction = manning`
*   `bedfricfile = manning_layer.dep`

![manning layer plot](/images/manning.png)

## Make waves

`MakeWaves.py` makes a single *jonswap* file based on a table of wave statistic observations. These observations likely come from downloaded data and should include wave height, period and direction along with timestamps. Assumes some pre-processing of downloaded data has already occurred (for example, extracting time series data from a single point or condensing an area of interest into a virtual buoy) and data have been saved as a .csv file. Might be useful for creating a single model based on a historical event.

## Make tides
Take a tide table and hammer it into a format that XBeach likes. Tide files may come from other tools such as [Coastsat](https://github.com/kvos/CoastSat), [PyFES](https://github.com/CNES/aviso-fes), or [pyTMD](https://github.com/pyTMD/pyTMD). Time series data should be saved in a .csv file. Here, two cases are covered: 
1) simple tide rises and falls evenly across the offshore boundary; 
2) offshore boundary corners out of phase inducing longshore currents (assumes rectangular domain).

![tides](/images/tides.png)