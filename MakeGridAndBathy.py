
"""
Create XBeach .grd and .dep files from bathymetry raster.
"""

# %% imports
import os
import pandas as pd
import numpy as np
import rasterio
from scipy.interpolate import RegularGridInterpolator
import matplotlib.pyplot as plt


# %% set paths
path = '/path_to_working_directory/'
depfile = 'BathymetryFile.tif'
os.chdir(path)


# %% load and plot bathy data
with rasterio.open(depfile) as src:
    bathy = src.read(1)
    nodata = src.nodata
    bathy = np.where(bathy == nodata, np.nan, bathy)
    extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]

plt.figure(figsize=(12, 8))
img = plt.imshow(bathy, extent=extent, origin='upper', cmap='viridis')
plt.colorbar(img, label='Elevation (m)')
plt.xlabel('Easting (m)')
plt.ylabel('Northing (m)')
plt.title('Original bathymetry')
plt.grid(alpha=0.3)


# %% describe region of interest
originEasting = 256400  # set origin easting
originNorthing = 638000 # set origin northing
distx = 600             # cross-shore dimension (m)
disty = 1200            # longshore dimension (m)
angle2beach = 90        # origin to beach measured COUNTERCLOCKWISE FROM EAST (deg.)


# %% calculate ROI based on inputs and plot to check
theta = np.radians(angle2beach)

c, s = np.cos(theta), np.sin(theta)
rotmat = np.array([
    [c, -s],
    [s,  c]
])

localROI = np.array([
    [0, 0],
    [distx, 0],
    [distx, disty],
    [0, disty],
    [0, 0]
])

worldROI = (rotmat @ localROI.T).T + [originEasting, originNorthing]
eastingROI = worldROI[:, 0]
northingROI = worldROI[:, 1]

plt.figure(figsize=(12, 8))
img = plt.imshow(bathy, extent=extent, origin='upper', cmap='viridis')
plt.plot(eastingROI, northingROI, 'r--', linewidth=2)
plt.scatter(eastingROI[:-1], northingROI[:-1], color='red', s=50)
plt.scatter(originEasting, originNorthing, color='yellow', s=75, zorder=2)
plt.colorbar(img, label='Elevation (m)')
plt.xlabel('Easting (m)')
plt.ylabel('Northing (m)')
plt.title('Proposed new grid area')
plt.grid(alpha=0.3)


# %% Define grid resolution in x-direction 
# X = 0 ALWAYS STARTS OFFSHORE AND X INCREASES MOVING TOWARD SHORE
offshoreRes = 10.0      # coarse resolution offshore (m)
nearshoreRes = 5.0      # finer resolution nearshore (m)
transitionStart = 200   # distance (m) from x=0 to start of transition zone
transitionStop = 300    # distance (m) from x=0 to end of transition zone


# %% create x grid resolution regions and plot to check
xFine = np.linspace(0, distx, distx + 1)
resProfileX = np.zeros_like(xFine)
resProfileX[xFine <= transitionStart] = offshoreRes
mask = (xFine > transitionStart) & (xFine <= transitionStop)
t = (xFine[mask] - transitionStart) / (transitionStop - transitionStart)

resProfileX[xFine <= transitionStart] = offshoreRes
resProfileX[mask] = nearshoreRes + (offshoreRes - nearshoreRes) * 0.5 * (1 + np.cos(np.pi * t))
resProfileX[xFine > transitionStop] = nearshoreRes

x_coords = [0.0]

while x_coords[-1] < distx:
    current_x = x_coords[-1]
    idx = np.argmin(np.abs(xFine - current_x))
    dx = resProfileX[idx]
    x_coords.append(current_x + dx)

actual_dist = x_coords[-1]
scale_factor = distx / actual_dist
intervals = np.diff(x_coords)
scaled_intervals = intervals * scale_factor

x_grid_1d = np.concatenate([[0], np.cumsum(scaled_intervals)])

plt.plot(xFine, resProfileX)
plt.xlabel('Cross shore distance (m)')
plt.ylabel('Grid resolution (m)')
plt.title('Grid resolution along x-axis (starts offshore)')
plt.show()


# %% Define grid resolution in y-direction 
# Y = 0 ALWAYS TO THE LEFT WHEN FACING OFFSHORE
sidesRes = 10.0             # coarse resolution near sides of study area (m)
centralRes = 5.0            # finer resolution near center (m)
transitionStart1 = 100      # distance (m) from y=0 to start of transition zone 1
transitionStop1  = 200      # distance (m) from y=0 to end of transition zone 1
transitionStart2 = 1000     # distance (m) from y=0 to start of transition zone 2
transitionStop2  = 1100     # distance (m) from y=0 to end of transition zone 2


# %% create x grid resolution regions and plot to check
yFine = np.linspace(0, disty, disty + 1)
resProfileY = np.zeros_like(yFine)
mask1 = (yFine > transitionStart1) & (yFine <= transitionStop1)
t1 = (yFine[mask1] - transitionStart1) / (transitionStop1 - transitionStart1)
mask2 = (yFine > transitionStart2) & (yFine <= transitionStop2)
t2 = (yFine[mask2] - transitionStart2) / (transitionStop2 - transitionStart2)

resProfileY[yFine <= transitionStart1] = sidesRes
resProfileY[mask1] = centralRes + (sidesRes - centralRes) * 0.5 * (1 + np.cos(np.pi * t1))
resProfileY[(yFine > transitionStop1) & (yFine <= transitionStart2)] = centralRes
resProfileY[mask2] = centralRes + (sidesRes - centralRes) * 0.5 * (1 - np.cos(np.pi * t2))
resProfileY[yFine > transitionStop2] = sidesRes

y_coords = [0.0]

while y_coords[-1] < disty:
    current_y = y_coords[-1]
    idx = np.argmin(np.abs(yFine - current_y))
    dy = resProfileY[idx]
    y_coords.append(current_y + dy)

actual_dist_y = y_coords[-1]
scale_factor_y = disty / actual_dist_y
intervals_y = np.diff(y_coords)
scaled_intervals_y = intervals_y * scale_factor_y

y_grid_1d = np.concatenate([[0], np.cumsum(scaled_intervals_y)])

plt.plot(yFine,resProfileY)
plt.xlabel('Alonghore distance (m)')
plt.ylabel('Grid resolution (m)')
plt.title('Grid resolution along y-axis (facing offshore)')
plt.show()


# %% plot full grid in UTM to check (set skip factor to adjust plotting density)
skip = 3

localX, localY = np.meshgrid(x_grid_1d, y_grid_1d)
localCoords = np.vstack([localX.ravel(), localY.ravel()])
worldGrid = (rotmat @ localCoords).T + [originEasting, originNorthing]
E_world = worldGrid[:, 0].reshape(localX.shape)
N_world = worldGrid[:, 1].reshape(localX.shape)

plt.figure(figsize=(10, 10))
plt.plot(E_world[::skip, :].T, N_world[::skip, :].T, 'k-', lw=0.5, alpha=0.3)
plt.plot(E_world[:, -1].T, N_world[:, -1].T, 'k-', lw=0.5, alpha=0.3)
plt.plot(E_world[:, ::skip], N_world[:, ::skip], 'k-', lw=0.5, alpha=0.3)
plt.plot(E_world[-1, :], N_world[-1, :], 'k-', lw=0.5, alpha=0.3)
plt.scatter(eastingROI[:-1], northingROI[:-1], color='red', s=50, zorder=2)
plt.scatter(originEasting, originNorthing, color='yellow', s=75, zorder=3)
plt.xlabel('Easting (m)')
plt.ylabel('Northing (m)')
plt.title("Projected model grid in UTM coordinates")
plt.axis('equal')
plt.show()


# %% interpolate bathymetry over grid and plot
cols = np.arange(src.width)
rows = np.arange(src.height)

vectorEasting, _ = rasterio.transform.xy(src.transform, [0]*len(cols), cols)
vectorEasting = np.array(vectorEasting)
_, vectorNorthing = rasterio.transform.xy(src.transform, rows, [0]*len(rows))
vectorNorthing = np.array(vectorNorthing)

if vectorNorthing[1] < vectorNorthing[0]:
    vectorNorthing = vectorNorthing[::-1]
    bathyOK = np.flipud(bathy)
else:
    bathyOK = bathy

interpFunc = RegularGridInterpolator(
    (vectorNorthing, vectorEasting),
    bathyOK,
    bounds_error=False,
    fill_value=np.nan
)

pts = np.column_stack([N_world.ravel(), E_world.ravel()])
Z_world_flat = interpFunc(pts)
Z_world = Z_world_flat.reshape(E_world.shape)
Z_world = np.nan_to_num(Z_world, nan=0.0)

plt.figure(figsize=(10, 8))
mesh = plt.pcolormesh(E_world, N_world, Z_world, shading='auto', cmap='terrain')
plt.colorbar(mesh, label='Elevation (m)')
plt.title(f'Model bathymetry $-$ nx = {Z_world.shape[1]-1}, ny = {Z_world.shape[0]-1}')
plt.xlabel('Easting (m)')
plt.ylabel('Northing (m)')
plt.axis('equal')
plt.show()


# %% save .grd and .dep files for XBeach
np.savetxt('x.grd', E_world, fmt='%.4f')
np.savetxt('y.grd', N_world, fmt='%.4f')
np.savetxt('bed.dep', Z_world, fmt='%.4f')
print(f".grd and .dep files saved to {path}.")