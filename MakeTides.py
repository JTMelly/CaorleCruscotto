"""
Generate tide files that XBeach can read.
Takes a tide.csv file as input, usually created by some other tool such as CoastSat (https://github.com/kvos/CoastSat), or PyFES (https://github.com/CNES/aviso-fes).
Two versions below: 
    1) simple tide moves perpendicular to shore;
    2) model corners offshore out of phase inducing tidal currents.
"""

# %% imports
import pandas as pd
import datetime as td
import os


# %% set wd and input tide file
workingDirectory = '/path_to_wd/'
tideFile = 'TideFile.csv'
os.chdir(workingDirectory)


"""
Case 1: simple tide moves perpendicular to shore
"""


# %% format dataframe
tides = pd.read_csv(tideFile)
tides.columns = ['datetime', 'tide']
tides['datetime'] = pd.to_datetime(tides['datetime'])
tides


# %% subset dataframe by time
startTime = '2024-01-01'
endTime = '2024-01-02'
trange = tides[tides['datetime'].between(startTime, endTime)].copy()
trange['elapsed'] = trange['datetime'] - trange['datetime'].min()
trange['elapsedseconds'] = trange['elapsed'].dt.total_seconds()
del tides
trange


# %% organize by XBeach expected columns
tideTable = trange[['elapsedseconds', 'tide', 'tide']]
tideTable.columns = ['secTot', 'tideL', 'tideR']
del trange
tideTable


# %% save text file for XBeach
tideTable.to_csv('tide.txt', sep=' ', index=False, header=False)


"""
Case 2: offshore corners out of phase inducing currents
"""


# %% settings
approachDir = 'L'                   # facing shore, flood tide approaches from 'L' (left) or 'R' (right)
alongshoreDist = 1000               # approximate alongshore domain measure in meters
maxSlope = 1*10e-5                  # play with this value to change current intensity
deltaH = alongshoreDist * maxSlope  # meters


# %% list of tide changes
tideDelt = []
delt0 = float(abs(tideTable['tideL'].values[1]-tideTable['tideL'].values[0]))
tideLn = float(tideTable['tideL'].values[0])
for i, tideLn1 in enumerate(tideTable['tideL']):
    if i == 0:
        tideDelt.append(delt0)
        continue
    tideDelt.append(abs(tideLn1-tideLn))
    tideLn = tideLn1

tideDeltRel = []
for i in enumerate (tideDelt):
    tideDeltRel.append(i[1]/max(tideDelt))

tideTable['changeRel'] = tideDeltRel


# %% new tide table with left and right offsets to induce current
tideTable2 = []
prevRawLeft = None

for time, rawLeft, rawRight, relChange in zip(tideTable['secTot'], tideTable['tideL'], tideTable['tideR'], tideTable['changeRel']):

    if time == 0:
        tideTable2.append([time, rawLeft, rawRight])
        prevRawLeft = rawLeft
        continue

    if rawLeft > prevRawLeft:
        current_state = 'FLOOD'
    elif rawLeft < prevRawLeft:
        current_state = 'EBB'
    else:
        current_state = 'SLACK'

    if approachDir == 'L':
        if current_state == 'FLOOD':
            left_out = rawLeft + deltaH * relChange / 2
            right_out = rawRight - deltaH * relChange / 2
        elif current_state == 'EBB':
            left_out = rawLeft - deltaH * relChange / 2
            right_out = rawRight + deltaH * relChange / 2
        else:
            left_out = rawLeft
            right_out = rawRight

    if approachDir == 'R':
        if current_state == 'FLOOD':
            left_out = rawLeft - deltaH * relChange / 2
            right_out = rawRight + deltaH * relChange / 2
        elif current_state == 'EBB':
            left_out = rawLeft + deltaH * relChange / 2
            right_out = rawRight - deltaH * relChange / 2
        else:
            left_out = rawLeft
            right_out = rawRight

    tideTable2.append([time, left_out, right_out])
    prevRawLeft = rawLeft


# %% format dataframe the way XBeach likes it
tideTable2 = pd.DataFrame(tideTable2, columns=['secTot', 'tideL', 'tideR'])
tideTable2['secTot'] = tideTable2['secTot'].round(1)
tideTable2['tideL'] = tideTable2['tideL'].round(3)
tideTable2['tideR'] = tideTable2['tideR'].round(3)
tideTable2

# %% plot result if desired
tideTable2.plot.line(x='secTot', y=['tideL', 'tideR'])


# %% save text file for Xbeach
tideTable2.to_csv('tide2.txt', sep=' ', index=False, header=False)