# CaorleCruscotto
Make XBeach models with Python.

## Make grid and bathymetry
`MakeGridAndBathy.py` takes a raster file containing elevation(depth) information and interpolates to a user-defined grid, outputting the .bed and .dep files that XBeach will look for to run. With [*rasterio*](https://github.com/rasterio/rasterio) and [*scipy*](https://github.com/scipy/scipy) under the hood, so far it has worked starting from .tif and .asc files. 

To use the generated files, update *params.txt* with:

*   `xfile        = x.grd`
*   `yfile        = y.grd`
*   `depfile      = bed.dep`

Also set `nx = _` and `ny = _` in *params.txt* accordingly (`nx` is always cross-shore and `ny` is always alongshore).