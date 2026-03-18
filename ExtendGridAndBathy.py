"""
Take existing .grd and .dep files and extend to target depth along user-defined slope.
"""


# %% imports
import os
import pandas as pd
import numpy as np
import rasterio
import matplotlib.pyplot as plt


# %% required user inputs
path = '/path_to_working_directory/'    # path to wd
x_grd_path = "x.grd"                    # x.grd file
y_grd_path = "y.grd"                    # y.grd file
bed_dep_path = "bed.dep"                # bed.dep file
angle2beach = 90                        # origin to beach angle COUNTERCLOCKWISE FROM EAST (deg.)
targetDepth = -20.0                     # required depth offshore
slope = 1/20                            # slope to reach target depth


# %% load files and gather variables
os.chdir(path)

E_world = np.loadtxt(x_grd_path)
N_world = np.loadtxt(y_grd_path)
Z_world = np.loadtxt(bed_dep_path)

row0_x = E_world[0, :]
row0_y = N_world[0, :]
x_grid_1d = np.sqrt((row0_x - row0_x[0])**2 + (row0_y - row0_y[0])**2)

col0_x = E_world[:, 0]
col0_y = N_world[:, 0]
y_grid_1d = np.sqrt((col0_x - col0_x[0])**2 + (col0_y - col0_y[0])**2)

originEasting = row0_x[0]
originNorthing = row0_y[0]

localROI = np.array([
    [0, 0],
    [x_grid_1d[-1], 0],
    [x_grid_1d[-1], y_grid_1d[-1]],
    [0, y_grid_1d[-1]],
    [0, 0]
])

theta = np.radians(angle2beach)

c, s = np.cos(theta), np.sin(theta)
rotmat = np.array([
    [c, -s],
    [s,  c]
])

print(f"Current grid shape: ({len(y_grid_1d)}, {len(x_grid_1d)})")
print(f"Angle to beach: {angle2beach} deg.")
print(f"Origin easting: {originEasting} m")
print(f"Origin northing: {originNorthing} m")
print(f"Current nx: {len(x_grid_1d)-1}")
print(f"Current ny: {len(y_grid_1d)-1}")


# %% extend existing grid in offshore direction and adjust model origin
dx = np.ceil(abs(x_grid_1d[1] - x_grid_1d[0]))

maxOffshoreZ = np.max(Z_world[0, :])
additionalDepth = abs(targetDepth - maxOffshoreZ)
minExtend = additionalDepth / slope
numNodes = int(np.ceil(minExtend / dx))
extensionLength = numNodes * dx

x_extend_1d = np.linspace(0, extensionLength, numNodes, endpoint=False)
x_grid_shifted = x_grid_1d + (extensionLength)
x_extended_1d = np.concatenate([x_extend_1d, x_grid_shifted])
X_loc_ext, Y_loc_ext = np.meshgrid(x_extended_1d, y_grid_1d)

shiftLocal = np.array([-extensionLength, 0])
shiftWorld = rotmat @ shiftLocal
originNewE = originEasting + shiftWorld[0]
originNewN = originNorthing + shiftWorld[1]

ExtLocalROI = np.array([
    [0, 0],
    [x_extended_1d[-1], 0],
    [x_extended_1d[-1], y_grid_1d[-1]],
    [0, y_grid_1d[-1]],
    [0, 0]
])

ExtWorldROI = (rotmat @ ExtLocalROI.T).T + [originNewE, originNewN]
ExtEastingROI = ExtWorldROI[:, 0]
ExtNorthingROI = ExtWorldROI[:, 1]

local_pts_ext = np.vstack([X_loc_ext.ravel(), Y_loc_ext.ravel()])
world_pts_ext = (rotmat @ local_pts_ext).T + [originNewE, originNewN]
E_world_ext = world_pts_ext[:, 0].reshape(X_loc_ext.shape)
N_world_ext = world_pts_ext[:, 1].reshape(X_loc_ext.shape)

print(f"New Grid Shape: {X_loc_ext.shape}")
print(f"Angle to beach: {angle2beach} deg.")
print(f"New origin easting: {originNewE} m")
print(f"New origin northing: {originNewN} m")
print(f"New nx: {X_loc_ext.shape[1] - 1}")
print(f"New ny: {X_loc_ext.shape[0] - 1}")


# %% plot to check extended grid (set skip factor to adjust grid density)
skip = 3

plt.figure(figsize=(10, 10))
plt.plot(E_world_ext[::skip, :].T, N_world_ext[::skip, :].T, 'k-', lw=0.5, alpha=0.3)
plt.plot(E_world_ext[:, -1].T, N_world_ext[:, -1].T, 'k-', lw=0.5, alpha=0.3)
plt.plot(E_world_ext[:, ::skip], N_world_ext[:, ::skip], 'k-', lw=0.5, alpha=0.3)
plt.plot(E_world_ext[-1, :], N_world_ext[-1, :], 'k-', lw=0.5, alpha=0.3)
plt.scatter(ExtEastingROI[:-1], ExtNorthingROI[:-1], color='red', s=50, zorder=2)
plt.scatter(originNewE, originNewN, color='yellow', s=75, zorder=3)

plt.xlabel('Easting (m)')
plt.ylabel('Northing (m)')
plt.title("Extended model grid in UTM coordinates")
plt.axis('equal')
plt.show()


# %% fill extended portion of grid with synthetic depth values
Z_world_ext = np.zeros((len(y_grid_1d), len(x_extended_1d)))

for i in range(len(y_grid_1d)):
    junction_z = Z_world[i, 0]
    z_slope = np.linspace(targetDepth, junction_z, numNodes, endpoint=False)
    Z_world_ext[i, :numNodes] = z_slope
    Z_world_ext[i, numNodes:] = Z_world[i, :]

print(f"Extended grid filled with synthetic bathymetry to {targetDepth} m.")


# %% plot to check cross-shore profiles
plt.figure()
plt.plot(X_loc_ext[:, :], Z_world_ext[:, :])
plt.ylabel('Elevation/depth (m)')
plt.xlabel('Cross-shore position (m)')
plt.title('Cross-shore profiles')
plt.show


# %% view extended bathymetry
plt.figure(figsize=(10, 8))
mesh = plt.pcolormesh(E_world_ext, N_world_ext, Z_world_ext, shading='auto', cmap='terrain')
plt.colorbar(mesh, label='Elevation (m)')
plt.title(f'Extended bathymetry $-$ nx = {Z_world_ext.shape[1]-1}, ny = {Z_world_ext.shape[0]-1}')
plt.xlabel('Easting (m)')
plt.ylabel('Northing (m)')
plt.axis('equal')
plt.show()


# %% save extended .grd and .dep files
np.savetxt('x_extended.grd', E_world_ext, fmt='%.4f')
np.savetxt('y_extended.grd', N_world_ext, fmt='%.4f')
np.savetxt('bed_extended.dep', Z_world_ext, fmt='%.4f')

print(f"Extended .grd and .dep files saved to {path}.")
