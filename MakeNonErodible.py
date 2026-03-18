"""
Make non-erodible layer file for XBeach based on existing bed.dep file.
"""


# %%
from shapely.geometry import Point
import matplotlib.pyplot as plt
from pathlib import Path
import geopandas as gpd
import numpy as np
import os


"""
Case 1: provide an erodible sediment thickness value that will be applied to the entire domain.
"""


# %% required user inputs
workingDir = '/home/jtm/Documents/Python/CaorleTestData/' # wd
depFile = 'bed.dep'                                       # bed.dep file
outFileName = 'ne_layer.dep'                              # output file name
sedDepth = 10                                             # erodible sediment thickness (m)


# %% save non-erodible file
fullPath = Path(workingDir) / depFile
outFile = Path(workingDir) / outFileName

if fullPath.exists():
  zVals = np.loadtxt(fullPath)
  neVals = np.full_like(zVals, fill_value=sedDepth)
  np.savetxt(outFile, neVals, fmt='%.3f')
  print(f'{outFile} saved.')
else:
  raise FileNotFoundError(f'File not found: {fullPath}.')


"""
Case 2: define erodible/non-erodible areas based on user-provided .geojson file.
Every grid node within the provided polygons will be assigned a value of 0.
Grid nodes external to the polygons will assume the user-defined value, below.
"""


# %% required user inputs
workingDir = '/path_to_working_directory/'  # wd
xGrid = 'x.grd'                             # x grid file
yGrid = 'y.grd'                             # y grid file
jsonFile = 'NonErodibleFile.geojson'        # .geojson file
outFileName = 'ne_layer.dep'                # output file name
UTMzone = '31N'                             # UTM zone
sedDepth = 50                               # erodible sediment thickness (m)


# %% check UTM zone and sediment thickness
zone_number = int(UTMzone[:-1])
hemisphere = UTMzone[-1].upper()

if hemisphere == "N":
  epsgCode = 32600 + zone_number
elif hemisphere == "S":
  epsgCode = 32700 + zone_number
else:
  raise ValueError("Invalid UTM zone format. Use format like '33N' or '33S'.")

print(f"Using EPSG: {epsgCode} for UTM Zone {UTMzone}.")
print(f"Erodible areas will be {sedDepth} m thick.")


# %% load grid and shapefiles, ensure CRSs match, save non-erodible layer file
x = np.loadtxt(Path(workingDir) / xGrid)
y = np.loadtxt(Path(workingDir) / yGrid)
nrows, ncols = x.shape

gdf = gpd.read_file(Path(workingDir) / jsonFile)

if gdf.crs == epsgCode:

    gdf = gdf.to_crs(epsg=epsgCode)
    nonErodibleGeometry = gdf.union_all()
    grid = np.full((nrows, ncols), sedDepth, dtype=np.float32)

    for i in range(nrows):
      for j in range(ncols):
        pt = Point(x[i, j], y[i, j])
        if nonErodibleGeometry.contains(pt):
            grid[i, j] = 0.0

    with open(Path(workingDir) / outFileName, 'w') as f:
      for row in grid:
        f.write(" ".join(f"{val:.1f}" for val in row) + "\n")

    print(f"{Path(workingDir) / outFileName} saved.")

elif gdf.crs is None:
    raise ValueError(".geojson has no embedded CRS.")
else:
    raise ValueError(".geojson CRS does not match expected CRS.")


# %% verify output by plotting
plt.figure(figsize=(10, 6))
pcm = plt.pcolormesh(x, y, grid, shading='auto', cmap='viridis')
plt.colorbar(pcm, label="Sediment thickness (m)")
gdf.boundary.plot(ax=plt.gca(), color='red', linestyle='--', linewidth=0.75)
plt.title("Check NE layer")
plt.xlabel("Easting [m]")
plt.ylabel("Northing [m]")
plt.xlim(x.min()-abs(x.max()-x.min())*0.05, x.max()+abs(x.max()-x.min())*0.05)
plt.ylim(y.min()-abs(y.max()-y.min())*0.05, y.max()+abs(y.max()-y.min())*0.05)
plt.grid(alpha=0.3)
plt.show()