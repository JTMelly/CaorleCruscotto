"""
Create a manning_layer.dep file based on an XBeach model bed.dep file.
Assigns Manning coefficient values to grid nodes based on polygons in a .geojson file.
.GEOJSON FILE MUST HAVE A FIELD NAMED "manning" holding the coefficient number values.
"""


# %% 
from shapely.geometry import Point
import matplotlib.pyplot as plt
from pathlib import Path
import geopandas as gpd
import numpy as np
import os


# %% required user inputs
workingDir = '/path_to_working_directory/'  # wd
xGrid = 'x.grd'                             # x grid file
yGrid = 'y.grd'                             # y grid file
jsonFile = 'ManningFile.geojson'            # MUST HAVE A "manning" FIELD WITH NUMBER VALUES
outFileName = 'manning_layer.dep'           # output file name
UTMzone = '31N'                             # UTM zone
defaultManning = 0.025                      # all other areas (dimensionless)


# %% check UTM zone and default coefficient value
zone_number = int(UTMzone[:-1])
hemisphere = UTMzone[-1].upper()

if hemisphere == "N":
  epsgCode = 32600 + zone_number
elif hemisphere == "S":
  epsgCode = 32700 + zone_number
else:
  raise ValueError("Invalid UTM zone format. Use format like '33N' or '33S'.")

print(f"Using EPSG: {epsgCode} for UTM Zone {UTMzone}.")
print(f"Default Manning coefficient for undefined areas: {defaultManning}.")


# %% load files, check CRSs match, save Manning file
x = np.loadtxt(Path(workingDir) / xGrid)
y = np.loadtxt(Path(workingDir) / yGrid)
nrows, ncols = x.shape

gdf = gpd.read_file(Path(workingDir) / jsonFile)

if gdf.crs == epsgCode:

  manningGrid = np.full((nrows, ncols), defaultManning, dtype=np.float32)

  for i in range(nrows):
    for j in range(ncols):
        pt = Point(x[i, j], y[i, j])
        for _, row in gdf.iterrows():
            if row.geometry.contains(pt):
                manningGrid[i, j] = float(row["manning"])
                break

  with open(Path(workingDir) / outFileName, 'w') as f:
    for row in manningGrid:
        f.write(" ".join(f"{val:.4f}" for val in row) + "\n")

  print(f"{Path(workingDir) / outFileName} saved.")

elif gdf.crs is None:
    raise ValueError(".geojson has no embedded CRS.")
else:
    raise ValueError(".geojson CRS does not match expected CRS.")


# %% plot to check
plt.figure(figsize=(10, 6))
pcm = plt.pcolormesh(x, y, manningGrid, shading='auto', cmap='YlGnBu')
plt.colorbar(pcm, label="Manning coefficients")
gdf.boundary.plot(ax=plt.gca(), color='red', linestyle='--', linewidth=0.75)
plt.title("Check Manning coefficients layer")
plt.xlabel("Easting [m]")
plt.xlim(x.min()-abs(x.max()-x.min())*.05, x.max()+abs(x.max()-x.min())*.05)
plt.ylabel("Northing [m]")
plt.ylim(y.min()-abs(y.max()-y.min())*.05, y.max()+abs(y.max()-y.min())*.05)
plt.grid(alpha=0.3)
plt.show()